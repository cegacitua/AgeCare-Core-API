from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ObservationCreate(BaseModel):
    category: str = "general"
    text: str
    photo_blob_path: Optional[str] = None


class ObservationResponse(BaseModel):
    id: str
    patient_id: str
    author_id: str
    author_name: Optional[str] = None
    category: str
    text: str
    photo_blob_path: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentCreate(BaseModel):
    type: str
    severity: str = "warning"
    occurred_at: datetime
    description: str


class IncidentResponse(BaseModel):
    id: str
    patient_id: str
    author_id: str
    author_name: Optional[str] = None
    type: str
    severity: str
    occurred_at: datetime
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HandoverNoteCreate(BaseModel):
    text: str


class HandoverNoteResponse(BaseModel):
    id: str
    patient_id: str
    author_id: str
    author_name: Optional[str] = None
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ElderCheckinCreate(BaseModel):
    feeling: str  # happy | neutral | sad | in_pain
    date: date


class ElderCheckinResponse(BaseModel):
    id: str
    patient_id: str
    feeling: str
    date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
