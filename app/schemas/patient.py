from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class PatientCreate(BaseModel):
    full_name: str
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    photo_url: Optional[str] = None
    conditions: Optional[List[str]] = []
    timezone: str = "America/Santiago"


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    photo_url: Optional[str] = None
    conditions: Optional[List[str]] = None
    timezone: Optional[str] = None


class PatientMemberResponse(BaseModel):
    id: str
    user_id: str
    patient_id: str
    role: str  # family | caregiver | doctor | elder
    is_owner: bool
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    member_id: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    status: str = "accepted"
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WearableStatusResponse(BaseModel):
    wearable_id: Optional[str] = "w-1"
    id: Optional[str] = "w-1"
    serial_number: Optional[str] = "WEAR-001"
    model: Optional[str] = "AgeCare Watch v1"
    battery_pct: int = 95
    last_sync_at: Optional[datetime] = None
    is_stale: bool = False
    is_online: bool = True

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(BaseModel):
    id: str
    patient_id: str  # Dual field for Flutter compatibility
    full_name: str
    birth_date: Optional[date] = date(1950, 1, 1)
    sex: Optional[str] = "M"
    photo_url: Optional[str] = None
    conditions: List[str] = []
    timezone: str = "America/Santiago"
    notes: Optional[str] = None
    wearable: Optional[WearableStatusResponse] = None
    created_at: datetime
    my_role: Optional[str] = "family"

    model_config = ConfigDict(from_attributes=True)


class PatientCardResponse(BaseModel):
    patient_id: str
    id: str
    full_name: str
    photo_url: Optional[str] = None
    role: str = "family"
    wellbeing_status: str = "ok"
    active_alerts_count: int = 0
    top_reason: Optional[str] = "Estado estable"

    model_config = ConfigDict(from_attributes=True)


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str  # family | caregiver | doctor | elder


class AcceptInvitationRequest(BaseModel):
    token: str


class WearableBindRequest(BaseModel):
    serial_number: str
    model: str
