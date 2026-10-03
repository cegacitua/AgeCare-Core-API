from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CareTaskCreate(BaseModel):
    category: str = "hygiene"
    title: str
    scheduled_at: datetime
    recurrence: Optional[str] = "daily"
    task_date: date


class CareTaskResponse(BaseModel):
    id: str
    patient_id: str
    category: str
    title: str
    scheduled_at: datetime
    recurrence: Optional[str] = None
    status: str  # pending | done | skipped
    done_by: Optional[str] = None
    done_at: Optional[datetime] = None
    task_date: date

    model_config = ConfigDict(from_attributes=True)


class CaregiverProfileCreateUpdate(BaseModel):
    headline: str
    bio: str
    years_experience: int = 0
    specialties: Optional[List[str]] = []
    languages: Optional[List[str]] = ["Español"]
    zones: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    is_listed: bool = True


class CaregiverProfileResponse(BaseModel):
    id: str
    profile_id: Optional[str] = None
    user_id: str
    name: Optional[str] = None
    photo_url: Optional[str] = None
    headline: str
    bio: str
    years_experience: int
    specialties: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    zones: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    is_listed: bool
    is_featured: bool
    rating: float = 0.0
    reviews_count: int
    price_per_hour: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class CaregiverSubscriptionResponse(BaseModel):
    user_id: str
    plan: str  # free | premium
    valid_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ActivatePremiumRequest(BaseModel):
    store: str = Field(..., description="app_store | play_store | web")
    purchase_token: str


class JobOfferResponse(BaseModel):
    id: str
    title: str
    description: str
    zone: str
    schedule: str
    pay_range: str
    contact_info: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
