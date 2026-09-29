from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class MarketplaceProductResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str
    photos: Optional[List[str]] = []
    price_range: str
    external_url: Optional[str] = None
    contact_info: str

    model_config = ConfigDict(from_attributes=True)


class CaregiverReviewCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class CaregiverReviewResponse(BaseModel):
    id: str
    profile_id: str
    author_id: str
    author_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactCaregiverRequest(BaseModel):
    message: str


class ContactRequestResponse(BaseModel):
    id: str
    profile_id: str
    family_user_id: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
