from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: str
    patient_id: str
    type: str  # fall | vital_out_of_range | missed_dose | sos | wearable_offline
    severity: str  # info | warning | critical
    title: str
    detail: str
    payload: Optional[Dict[str, Any]] = None
    status: str  # pending | acknowledged | resolved
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResolveAlertRequest(BaseModel):
    note: Optional[str] = None


class NotificationSettingResponse(BaseModel):
    user_id: str
    alert_type: str
    push_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class NotificationSettingUpdate(BaseModel):
    alert_type: str
    push_enabled: bool


class TriggerSOSRequest(BaseModel):
    note: Optional[str] = None


class SOSEventResponse(BaseModel):
    id: str
    patient_id: str
    triggered_by: str
    note: Optional[str] = None
    alert_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
