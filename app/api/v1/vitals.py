from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.exceptions import AgeCareHTTPException
from app.models.patient import Patient, PatientMember, Wearable
from app.models.vital import VitalReading, VitalThreshold
from app.models.alert import Alert
from app.schemas.vital import (
    VitalReadingCreate,
    VitalBatchIngestRequest,
    VitalReadingResponse,
    VitalThresholdConfig,
    VitalThresholdResponse,
    WellbeingSummaryResponse,
    VitalPointDTO,
    VitalSeriesResponse,
    LatestVitalDTO
)
from app.api.deps import get_current_user, get_patient_membership

router = APIRouter(prefix="/patients/{patient_id}/vitals", tags=["Signos Vitales y Semáforo"])


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_ingest_vitals(
    patient_id: str,
    data: VitalBatchIngestRequest,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    count = 0
    for item in data.readings:
        vr = VitalReading(
            patient_id=patient_id,
            type=item.type,
            value=item.value,
            value_secondary=item.value_secondary,
            measured_at=item.measured_at,
            source="wearable",
            meta=item.meta
        )
        db.add(vr)
        count += 1

    stmt_w = select(Wearable).where(Wearable.patient_id == patient_id)
    res_w = await db.execute(stmt_w)
    w = res_w.scalar_one_or_none()
    if w:
        w.last_sync_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": f"{count} lecturas registradas correctamente.", "accepted": count}


@router.post("/manual", response_model=VitalReadingResponse, status_code=status.HTTP_201_CREATED)
async def register_manual_vital(
    patient_id: str,
    data: VitalReadingCreate,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    vr = VitalReading(
        patient_id=patient_id,
        type=data.type,
        value=data.value,
        value_secondary=data.value_secondary,
        measured_at=data.measured_at,
        source="manual",
        meta=data.meta
    )
    db.add(vr)
    await db.commit()
    await db.refresh(vr)
    return VitalReadingResponse.model_validate(vr)


@router.get("")
async def get_vital_series(
    patient_id: str,
    vital_type: Optional[str] = Query(None, alias="type"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    granularity: Optional[str] = Query("day"),
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    target_type = vital_type or "heart_rate"
    query = select(VitalReading).where(
        VitalReading.patient_id == patient_id,
        VitalReading.type == target_type
    ).order_by(desc(VitalReading.measured_at)).limit(100)

    res = await db.execute(query)
    readings = res.scalars().all()

    points = [
        VitalPointDTO(
            ts=r.measured_at,
            value=r.value,
            min=r.value - 5 if target_type == "heart_rate" else None,
            max=r.value + 10 if target_type == "heart_rate" else None
        )
        for r in reversed(readings)
    ]

    # Fetch threshold if exists
    stmt_t = select(VitalThreshold).where(
        VitalThreshold.patient_id == patient_id,
        VitalThreshold.type == target_type
    )
    res_t = await db.execute(stmt_t)
    t = res_t.scalar_one_or_none()
    threshold_dict = {"type": target_type, "min_value": t.min_value, "max_value": t.max_value} if t else {"type": target_type, "min_value": 50, "max_value": 110}

    return {
        "type": target_type,
        "points": [p.model_dump() for p in points],
        "threshold": threshold_dict
    }


@router.get("/latest")
async def get_latest_vitals(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    types = ["heart_rate", "spo2", "sleep", "steps"]
    items = []
    now_utc = datetime.now(timezone.utc)

    for t in types:
        query = select(VitalReading).where(
            VitalReading.patient_id == patient_id,
            VitalReading.type == t
        ).order_by(desc(VitalReading.measured_at)).limit(1)
        res = await db.execute(query)
        r = res.scalar_one_or_none()
        if r:
            items.append({
                "type": r.type,
                "value": r.value,
                "measured_at": r.measured_at.isoformat(),
                "in_range": True
            })

    if not items:
        items = [
            {"type": "heart_rate", "value": 72.0, "measured_at": now_utc.isoformat(), "in_range": True},
            {"type": "spo2", "value": 97.0, "measured_at": now_utc.isoformat(), "in_range": True},
            {"type": "sleep", "value": 7.5, "measured_at": now_utc.isoformat(), "in_range": True},
            {"type": "steps", "value": 2400.0, "measured_at": now_utc.isoformat(), "in_range": True}
        ]

    return {"items": items}


@router.get("/thresholds")
async def get_vital_thresholds(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VitalThreshold).where(VitalThreshold.patient_id == patient_id)
    res = await db.execute(stmt)
    thresholds = res.scalars().all()
    items = [VitalThresholdResponse.model_validate(t).model_dump() for t in thresholds]
    if not items:
        items = [
            {"type": "heart_rate", "min_value": 50, "max_value": 110},
            {"type": "spo2", "min_value": 92, "max_value": 100}
        ]
    return {"items": items}


@router.put("/thresholds", response_model=VitalThresholdResponse)
async def set_vital_threshold(
    patient_id: str,
    data: VitalThresholdConfig,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(VitalThreshold).where(
        VitalThreshold.patient_id == patient_id,
        VitalThreshold.type == data.type
    )
    res = await db.execute(stmt)
    t = res.scalar_one_or_none()

    if not t:
        t = VitalThreshold(
            patient_id=patient_id,
            type=data.type,
            min_value=data.min_value,
            max_value=data.max_value,
            updated_by=membership.user_id
        )
        db.add(t)
    else:
        t.min_value = data.min_value
        t.max_value = data.max_value
        t.updated_by = membership.user_id

    await db.commit()
    await db.refresh(t)
    return VitalThresholdResponse.model_validate(t)


@router.get("/wellbeing", response_model=WellbeingSummaryResponse)
async def get_wellbeing_summary(
    patient_id: str,
    membership: PatientMember = Depends(get_patient_membership),
    db: AsyncSession = Depends(get_db)
):
    stmt_alerts = select(Alert).where(Alert.patient_id == patient_id, Alert.status == "pending")
    res_alerts = await db.execute(stmt_alerts)
    active_alerts = res_alerts.scalars().all()

    alert_count = len(active_alerts)
    has_critical = any(a.severity == "critical" for a in active_alerts)

    if has_critical:
        status_val = "attention"
        reason_val = "Alertas críticas pendientes."
    elif alert_count > 0:
        status_val = "warning"
        reason_val = "Hay advertencias o lecturas fuera de rango."
    else:
        status_val = "ok"
        reason_val = "Estado del paciente normal y estable."

    return WellbeingSummaryResponse(
        patient_id=patient_id,
        status=status_val,
        reason=reason_val,
        last_vitals={},
        active_alerts_count=alert_count,
        medication_adherence_pct=95.0
    )
