from datetime import date, datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import PatientMember
from app.models.caregiver import CareTask, CaregiverProfile, CaregiverSubscription, JobOffer
from app.schemas.caregiver import (
    CareTaskCreate,
    CareTaskResponse,
    CaregiverProfileCreateUpdate,
    CaregiverProfileResponse,
    CaregiverSubscriptionResponse,
    ActivatePremiumRequest,
    JobOfferResponse
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(prefix="/caregiver", tags=["Vista de la Cuidadora y Gestión Profesional"])


@router.get("/tasks", response_model=List[CareTaskResponse])
async def list_daily_tasks(
    patient_id: str,
    target_date: Optional[date] = Query(None, alias="date"),
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    query = select(CareTask).where(CareTask.patient_id == patient_id)
    if target_date:
        query = query.where(CareTask.task_date == target_date)
    query = query.order_by(CareTask.scheduled_at)

    res = await db.execute(query)
    tasks = res.scalars().all()
    return [CareTaskResponse.model_validate(t) for t in tasks]


@router.post("/tasks", response_model=CareTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_care_task(
    patient_id: str,
    data: CareTaskCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    task = CareTask(
        patient_id=patient_id,
        category=data.category,
        title=data.title,
        scheduled_at=data.scheduled_at,
        recurrence=data.recurrence,
        task_date=data.task_date,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return CareTaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/toggle", response_model=CareTaskResponse)
async def toggle_care_task(
    task_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CareTask).where(CareTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="La tarea no existe.")

    if task.status == "done":
        task.status = "pending"
        task.done_by = None
        task.done_at = None
    else:
        task.status = "done"
        task.done_by = membership.user_id
        task.done_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)
    return CareTaskResponse.model_validate(task)


@router.get("/profile", response_model=CaregiverProfileResponse)
async def get_my_caregiver_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        prof = CaregiverProfile(
            user_id=current_user.id,
            headline="Cuidadora Profesional de Adultos Mayores",
            bio="Tengo experiencia en cuidado de adultos mayores, administración de medicamentos y primeros auxilios.",
            years_experience=3,
            specialties=["Primeros Auxilios", "Movilidad Reducida"],
            languages=["Español"],
            zones=["Providencia", "Las Condes"],
            is_listed=True
        )
        db.add(prof)
        await db.commit()
        await db.refresh(prof)

    out = CaregiverProfileResponse.model_validate(prof)
    out.user_name = current_user.full_name
    return out


@router.put("/profile", response_model=CaregiverProfileResponse)
async def update_my_caregiver_profile(
    data: CaregiverProfileCreateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverProfile).where(CaregiverProfile.user_id == current_user.id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()

    if not prof:
        prof = CaregiverProfile(user_id=current_user.id, **data.model_dump())
        db.add(prof)
    else:
        for k, v in data.model_dump().items():
            setattr(prof, k, v)

    await db.commit()
    await db.refresh(prof)

    out = CaregiverProfileResponse.model_validate(prof)
    out.user_name = current_user.full_name
    return out


@router.get("/subscription", response_model=CaregiverSubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverSubscription).where(CaregiverSubscription.user_id == current_user.id)
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()

    if not sub:
        sub = CaregiverSubscription(user_id=current_user.id, plan="free")
        db.add(sub)
        await db.commit()
        await db.refresh(sub)

    return CaregiverSubscriptionResponse.model_validate(sub)


@router.post("/subscription/premium", response_model=CaregiverSubscriptionResponse)
async def activate_premium(
    data: ActivatePremiumRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CaregiverSubscription).where(CaregiverSubscription.user_id == current_user.id)
    res = await db.execute(stmt)
    sub = res.scalar_one_or_none()

    if not sub:
        sub = CaregiverSubscription(
            user_id=current_user.id,
            plan="premium",
            store=data.store,
            purchase_token=data.purchase_token,
            valid_until=datetime.now(timezone.utc) + timedelta(days=365)
        )
        db.add(sub)
    else:
        sub.plan = "premium"
        sub.store = data.store
        sub.purchase_token = data.purchase_token
        sub.valid_until = datetime.now(timezone.utc) + timedelta(days=365)

    await db.commit()
    await db.refresh(sub)
    return CaregiverSubscriptionResponse.model_validate(sub)


@router.get("/job-offers", response_model=List[JobOfferResponse])
async def list_job_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(JobOffer).where(JobOffer.is_active == True).order_by(desc(JobOffer.created_at))
    res = await db.execute(stmt)
    offers = res.scalars().all()
    if not offers:
        sample = JobOffer(
            title="Cuidado de turno noche en Las Condes",
            description="Se busca cuidadora experimentada para apoyo en medicamentos y compañía nocturna.",
            zone="Las Condes, Santiago",
            schedule="Lunes a Viernes 20:00 - 08:00",
            pay_range="$45.000 / turno",
            contact_info="contacto@familia.cl"
        )
        return [JobOfferResponse.model_validate(sample)]
    return [JobOfferResponse.model_validate(o) for o in offers]
