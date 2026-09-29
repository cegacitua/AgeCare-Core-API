from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    phone: Optional[str] = None
    locale: str = "es-CL"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: Optional[str] = None


class MembershipDTO(BaseModel):
    patient_id: str
    patient_name: str
    role: str


class UserResponse(BaseModel):
    id: str
    user_id: str  # Dual field for Flutter compatibility
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: str = "es"
    created_at: datetime
    memberships: List[MembershipDTO] = []

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    user_id: Optional[str] = None  # For register compatibility in Flutter
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 mins
    user: UserResponse
    roles: Optional[Dict[str, str]] = None
    memberships: List[MembershipDTO] = []


class PushDeviceRegister(BaseModel):
    push_token: Optional[str] = None
    token: Optional[str] = None
    platform: str = Field(default="android", description="android | ios | web")
