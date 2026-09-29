from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import PatientMember
from app.models.observation import Observation, Incident, HandoverNote, ElderCheckin
from app.schemas.observation import (
    ObservationCreate,
    ObservationResponse,
    IncidentCreate,
    IncidentResponse,
    HandoverNoteCreate,
    HandoverNoteResponse,
    ElderCheckinCreate,
    ElderCheckinResponse
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(prefix="/patients/{patient_id}", tags=["Bitácora, Incidentes y Relevos"])


@router.post("/observations", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def create_observation(
    patient_id: str,
    data: ObservationCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    obs = Observation(
        patient_id=patient_id,
        author_id=membership.user_id,
        category=data.category,
        text=data.text,
        photo_blob_path=data.photo_blob_path
    )
    db.add(obs)
    await db.commit()
    await db.refresh(obs)

    res = ObservationResponse.model_validate(obs)
    res.author_name = membership.user.full_name if membership.user else "Cuidadora"
    return res


@router.get("/observations", response_model=List[ObservationResponse])
async def list_observations(
    patient_id: str,
    category: Optional[str] = Query(None),
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    query = select(Observation, User).join(User, Observation.author_id == User.id).where(
        Observation.patient_id == patient_id
    )
    if category:
        query = query.where(Observation.category == category)
    query = query.order_by(desc(Observation.created_at)).limit(100)

    res = await db.execute(query)
    rows = res.all()

    out = []
    for obs, user in rows:
        r = ObservationResponse.model_validate(obs)
        r.author_name = user.full_name
        out.append(r)
    return out


@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    patient_id: str,
    data: IncidentCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    inc = Incident(
        patient_id=patient_id,
        author_id=membership.user_id,
        type=data.type,
        severity=data.severity,
        occurred_at=data.occurred_at,
        description=data.description
    )
    db.add(inc)
    await db.commit()
    await db.refresh(inc)

    res = IncidentResponse.model_validate(inc)
    res.author_name = membership.user.full_name if membership.user else "Cuidadora"
    return res


@router.post("/handovers", response_model=HandoverNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_handover_note(
    patient_id: str,
    data: HandoverNoteCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    hn = HandoverNote(
        patient_id=patient_id,
        author_id=membership.user_id,
        text=data.text
    )
    db.add(hn)
    await db.commit()
    await db.refresh(hn)

    res = HandoverNoteResponse.model_validate(hn)
    res.author_name = membership.user.full_name if membership.user else "Cuidadora"
    return res


@router.get("/handovers", response_model=List[HandoverNoteResponse])
async def list_handover_notes(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(HandoverNote, User).join(User, HandoverNote.author_id == User.id).where(
        HandoverNote.patient_id == patient_id
    ).order_by(desc(HandoverNote.created_at)).limit(50)

    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for hn, user in rows:
        r = HandoverNoteResponse.model_validate(hn)
        r.author_name = user.full_name
        out.append(r)
    return out


@router.post("/elder-checkin", response_model=ElderCheckinResponse)
async def register_elder_checkin(
    patient_id: str,
    data: ElderCheckinCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ElderCheckin).where(
        ElderCheckin.patient_id == patient_id,
        ElderCheckin.date == data.date
    )
    res = await db.execute(stmt)
    ec = res.scalar_one_or_none()

    if not ec:
        ec = ElderCheckin(
            patient_id=patient_id,
            feeling=data.feeling,
            date=data.date
        )
        db.add(ec)
    else:
        ec.feeling = data.feeling

    await db.commit()
    await db.refresh(ec)
    return ElderCheckinResponse.model_validate(ec)
