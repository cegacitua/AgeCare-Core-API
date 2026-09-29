from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.user import User
from app.models.patient import PatientMember
from app.models.alert import Alert, NotificationSetting, SOSEvent
from app.schemas.alert import (
    AlertResponse,
    ResolveAlertRequest,
    NotificationSettingResponse,
    NotificationSettingUpdate,
    TriggerSOSRequest,
    SOSEventResponse
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(tags=["Alertas y Notificaciones"])


@router.get("/patients/{patient_id}/alerts", response_model=List[AlertResponse])
async def list_patient_alerts(
    patient_id: str,
    alert_status: Optional[str] = Query(None, alias="status"),
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    query = select(Alert).where(Alert.patient_id == patient_id)
    if alert_status:
        query = query.where(Alert.status == alert_status)
    query = query.order_by(desc(Alert.created_at)).limit(100)

    res = await db.execute(query)
    alerts = res.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="La alerta no existe.")

    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    data: ResolveAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == alert_id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise AgeCareHTTPException(status_code=404, code="NOT_FOUND", message="La alerta no existe.")

    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolution_note = data.note
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)


@router.get("/notifications/settings", response_model=List[NotificationSettingResponse])
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    res = await db.execute(stmt)
    settings_list = res.scalars().all()
    return [NotificationSettingResponse.model_validate(s) for s in settings_list]


@router.put("/notifications/settings", response_model=NotificationSettingResponse)
async def update_notification_setting(
    data: NotificationSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationSetting).where(
        NotificationSetting.user_id == current_user.id,
        NotificationSetting.alert_type == data.alert_type
    )
    res = await db.execute(stmt)
    setting = res.scalar_one_or_none()

    if not setting:
        setting = NotificationSetting(
            user_id=current_user.id,
            alert_type=data.alert_type,
            push_enabled=data.push_enabled
        )
        db.add(setting)
    else:
        setting.push_enabled = data.push_enabled

    await db.commit()
    await db.refresh(setting)
    return NotificationSettingResponse.model_validate(setting)


@router.post("/patients/{patient_id}/sos", response_model=SOSEventResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    patient_id: str,
    data: TriggerSOSRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    # 1. Create SOS Alert
    sos_alert = Alert(
        patient_id=patient_id,
        type="sos",
        severity="critical",
        title="¡EMERGENCIA SOS ACTIVADA!",
        detail=f"El usuario {membership.user.full_name if membership.user else 'Adulto mayor'} ha presionado el botón SOS. {data.note or ''}",
        status="pending"
    )
    db.add(sos_alert)
    await db.flush()

    # 2. Create SOS Event
    event = SOSEvent(
        patient_id=patient_id,
        triggered_by=membership.user_id,
        note=data.note,
        alert_id=sos_alert.id
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return SOSEventResponse.model_validate(event)
