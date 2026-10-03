from datetime import timedelta
from datetime import datetime, timezone, date
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import Patient, PatientMember, Invitation, Wearable
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientCardResponse,
    PatientMemberResponse,
    InviteMemberRequest,
    AcceptInvitationRequest,
    WearableBindRequest,
    WearableStatusResponse
)
from app.schemas.vital import TodaySummaryResponse, SummaryHighlightDTO
from app.api.deps import get_current_user, get_patient_membership, require_patient_roles

router = APIRouter(tags=["Pacientes y Círculo de Cuidado"])


def _build_patient_response(pat: Patient, my_role: str = "family", wearable: Wearable = None) -> PatientResponse:
    wearable_dto = None
    if wearable:
        wearable_dto = WearableStatusResponse(
            wearable_id=wearable.id,
            id=wearable.id,
            serial_number=wearable.serial_number,
            model=wearable.model,
            battery_pct=wearable.battery_pct,
            last_sync_at=wearable.last_sync_at,
            is_stale=False,
            is_online=True
        )

    return PatientResponse(
        id=pat.id,
        patient_id=pat.id,
        full_name=pat.full_name,
        birth_date=pat.birth_date or date(1950, 1, 1),
        sex=pat.sex or "M",
        photo_url=pat.photo_url,
        conditions=pat.conditions or [],
        timezone=pat.timezone or "America/Santiago",
        notes=None,
        wearable=wearable_dto,
        created_at=pat.created_at,
        my_role=my_role
    )


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    patient = Patient(
        full_name=data.full_name,
        birth_date=data.birth_date or date(1950, 1, 1),
        sex=data.sex or "M",
        photo_url=data.photo_url,
        conditions=data.conditions or [],
        timezone=data.timezone
    )
    db.add(patient)
    await db.flush()

    membership = PatientMember(
        patient_id=patient.id,
        user_id=current_user.id,
        role="family",
        is_owner=True
    )
    db.add(membership)
    await db.commit()
    await db.refresh(patient)

    return _build_patient_response(patient, my_role="family")


@router.get("/patients")
async def list_my_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PatientMember, Patient).join(Patient, PatientMember.patient_id == Patient.id).where(
        PatientMember.user_id == current_user.id,
        Patient.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for member, pat in rows:
        items.append(
            PatientCardResponse(
                patient_id=pat.id,
                id=pat.id,
                full_name=pat.full_name,
                photo_url=pat.photo_url,
                role=member.role,
                wellbeing_status="ok",
                active_alerts_count=0,
                top_reason="Estado estable"
            )
        )
    return {"items": items}


@router.get("/users/me/dashboard")
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await list_my_patients(current_user, db)


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient_detail(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).where(Patient.id == patient_id, Patient.deleted_at.is_(None))
    res = await db.execute(stmt)
    pat = res.scalar_one_or_none()
    if not pat:
        raise AgeCareHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="El paciente no existe."
        )

    stmt_w = select(Wearable).where(Wearable.patient_id == patient_id)
    res_w = await db.execute(stmt_w)
    wearable = res_w.scalar_one_or_none()

    return _build_patient_response(pat, my_role=membership.role, wearable=wearable)


@router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    membership: PatientMember = Depends(require_patient_roles(["family"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).where(Patient.id == patient_id, Patient.deleted_at.is_(None))
    res = await db.execute(stmt)
    pat = res.scalar_one_or_none()
    if not pat:
        raise AgeCareHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="El paciente no existe."
        )

    if data.full_name is not None: pat.full_name = data.full_name
    if data.birth_date is not None: pat.birth_date = data.birth_date
    if data.sex is not None: pat.sex = data.sex
    if data.photo_url is not None: pat.photo_url = data.photo_url
    if data.conditions is not None: pat.conditions = data.conditions
    if data.timezone is not None: pat.timezone = data.timezone

    await db.commit()
    await db.refresh(pat)
    return _build_patient_response(pat, my_role=membership.role)


@router.get("/patients/{patient_id}/summary/today", response_model=TodaySummaryResponse)
async def get_patient_today_summary(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).where(Patient.id == patient_id)
    res = await db.execute(stmt)
    pat = res.scalar_one_or_none()
    pat_name = pat.full_name if pat else "El paciente"

    # 1. Alertas
    from app.models.alert import Alert
    stmt_alerts = select(Alert).where(Alert.patient_id == patient_id, Alert.status == "pending")
    res_alerts = await db.execute(stmt_alerts)
    alerts = res_alerts.scalars().all()
    active_alerts_count = len(alerts)
    
    status_val = "ok"
    top_reason = "Sin alertas registradas"
    summary = f"{pat_name} se encuentra en estado estable y dentro de los rangos normales."
    
    if any(a.severity == "critical" for a in alerts):
        status_val = "attention"
        top_reason = "Alerta crítica"
        summary = f"{pat_name} requiere atención inmediata debido a alertas críticas."
    elif active_alerts_count > 0:
        status_val = "warning"
        top_reason = alerts[0].title
        summary = f"{pat_name} presenta algunas advertencias que requieren revisión."

    # 2. Adherencia a medicamentos (Hoy)
    from app.models.medication import ScheduledDose
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    stmt_doses = select(ScheduledDose).where(
        ScheduledDose.patient_id == patient_id,
        ScheduledDose.scheduled_at >= today_start
    )
    res_doses = await db.execute(stmt_doses)
    doses = res_doses.scalars().all()
    total_doses = len(doses)
    taken_doses = sum(1 for d in doses if d.status == "taken")
    adherence_pct = int((taken_doses / total_doses * 100)) if total_doses > 0 else 100

    # 3. Signos vitales más recientes
    from app.models.vital import VitalReading
    stmt_hr = select(VitalReading).where(VitalReading.patient_id == patient_id, VitalReading.type == "heart_rate").order_by(VitalReading.measured_at.desc()).limit(1)
    stmt_steps = select(VitalReading).where(VitalReading.patient_id == patient_id, VitalReading.type == "steps").order_by(VitalReading.measured_at.desc()).limit(1)
    
    hr_res = (await db.execute(stmt_hr)).scalar_one_or_none()
    steps_res = (await db.execute(stmt_steps)).scalar_one_or_none()
    
    hr_val = f"{int(hr_res.value)} lpm" if hr_res else "--"
    steps_val = f"{int(steps_res.value)}" if steps_res else "--"

    return TodaySummaryResponse(
        wellbeing_status=status_val,
        date=datetime.now(timezone.utc),
        summary=summary,
        top_reason=top_reason,
        active_alerts_count=active_alerts_count,
        adherence_pct=adherence_pct,
        highlights=[
            SummaryHighlightDTO(icon_key="heart", icon="heart", label="Ritmo cardíaco", value=hr_val),
            SummaryHighlightDTO(icon_key="steps", icon="steps", label="Pasos", value=steps_val),
            SummaryHighlightDTO(icon_key="medication", icon="medication", label="Adherencia", value=f"{adherence_pct}%")
        ],
        latest_vitals=[]
    )


@router.post("/patients/{patient_id}/invitations")
async def invite_member_to_patient(
    patient_id: str,
    data: InviteMemberRequest,
    membership: PatientMember = Depends(require_patient_roles(["family"])),
    db: AsyncSession = Depends(get_db)
):
    raw_token = f"inv_{uuid.uuid4().hex}"
    inv = Invitation(
        patient_id=patient_id,
        email=data.email.lower(),
        role=data.role,
        token_hash=get_password_hash(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(inv)
    await db.commit()

    return {
        "invitation_id": inv.id,
        "token": raw_token,
        "invite_url": f"https://app.agecare.app/invite/{raw_token}",
        "expires_at": inv.expires_at.isoformat()
    }


@router.post("/invitations/accept")
async def accept_invitation(
    data: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Invitation).where(Invitation.expires_at > datetime.now(timezone.utc))
    res = await db.execute(stmt)
    invitations = res.scalars().all()

    matched_inv = None
    for inv in invitations:
        if get_password_hash(data.token) == inv.token_hash or inv.email.lower() == current_user.email.lower():
            matched_inv = inv
            break

    if not matched_inv:
        raise AgeCareHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_INVITATION",
            message="La invitación es inválida o ha expirado."
        )

    mem = PatientMember(
        patient_id=matched_inv.patient_id,
        user_id=current_user.id,
        role=matched_inv.role,
        is_owner=False
    )
    db.add(mem)
    matched_inv.accepted_by = current_user.id
    await db.commit()

    return {"message": "Te has unido al círculo de cuidado exitosamente."}


@router.get("/patients/{patient_id}/members", response_model=List[PatientMemberResponse])
async def list_circle_of_care(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PatientMember, User).join(User, PatientMember.user_id == User.id).where(
        PatientMember.patient_id == patient_id
    )
    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for mem, user in rows:
        m_res = PatientMemberResponse.model_validate(mem)
        m_res.user_name = user.full_name
        m_res.user_email = user.email
        out.append(m_res)
    return out


@router.post("/patients/{patient_id}/wearable", response_model=WearableStatusResponse)
async def bind_wearable(
    patient_id: str,
    data: WearableBindRequest,
    membership: PatientMember = Depends(require_patient_roles(["family", "caregiver"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Wearable).where(Wearable.patient_id == patient_id)
    res = await db.execute(stmt)
    wearable = res.scalar_one_or_none()

    if not wearable:
        wearable = Wearable(
            patient_id=patient_id,
            serial_number=data.serial_number,
            model=data.model,
            battery_pct=95,
            last_sync_at=datetime.now(timezone.utc)
        )
        db.add(wearable)
    else:
        wearable.serial_number = data.serial_number
        wearable.model = data.model
        wearable.last_sync_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(wearable)
    return WearableStatusResponse(
        wearable_id=wearable.id,
        id=wearable.id,
        serial_number=wearable.serial_number,
        model=wearable.model,
        battery_pct=wearable.battery_pct,
        last_sync_at=wearable.last_sync_at,
        is_stale=False,
        is_online=True
    )


@router.get("/patients/{patient_id}/wearable/status", response_model=WearableStatusResponse)
@router.get("/patients/{patient_id}/wearable/sync", response_model=WearableStatusResponse)
async def get_wearable_sync_status(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Wearable).where(Wearable.patient_id == patient_id)
    res = await db.execute(stmt)
    wearable = res.scalar_one_or_none()

    if not wearable:
        return WearableStatusResponse(
            wearable_id=None,
            id=None,
            serial_number="N/A",
            model="No vinculado",
            battery_pct=0,
            last_sync_at=None,
            is_stale=True,
            is_online=False
        )

    return WearableStatusResponse(
        wearable_id=wearable.id,
        id=wearable.id,
        serial_number=wearable.serial_number,
        model=wearable.model,
        battery_pct=wearable.battery_pct,
        last_sync_at=wearable.last_sync_at,
        is_stale=False,
        is_online=True
    )
