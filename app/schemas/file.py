from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UploadUrlRequest(BaseModel):
    purpose: str = Field(..., description="avatar | medical_doc | photo | audio")
    filename: str
    content_type: str
    size_bytes: int


class UploadUrlResponse(BaseModel):
    upload_id: str
    upload_url: str
    blob_path: str
    expires_in_sec: int = 3600


class DocumentCreate(BaseModel):
    upload_id: str
    title: str
    category: str = "prescription"
    doc_date: Optional[date] = None


class DocumentResponse(BaseModel):
    id: str
    patient_id: str
    upload_id: str
    title: str
    category: str
    doc_date: Optional[date] = None
    uploaded_by: str
    blob_path: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
