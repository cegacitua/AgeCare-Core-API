from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SharePhotoRequest(BaseModel):
    upload_id: str
    caption: Optional[str] = None


class ReactionRequest(BaseModel):
    kind: str  # heart | voice
    voice_blob_path: Optional[str] = None


class PhotoReactionResponse(BaseModel):
    id: str
    photo_id: str
    user_id: str
    user_name: Optional[str] = None
    kind: str
    voice_blob_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PhotoResponse(BaseModel):
    id: str
    patient_id: str
    upload_id: str
    shared_by: str
    shared_by_name: Optional[str] = None
    caption: Optional[str] = None
    url: Optional[str] = None
    reactions: List[PhotoReactionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentItemResponse(BaseModel):
    id: str
    kind: str  # joke | news
    title: str
    body: str
    source: Optional[str] = None
    audio_blob_path: Optional[str] = None
    locale: str
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TTSRequest(BaseModel):
    text: str
    voice: str = "es-CL-PalomaNeural"


class TTSResponse(BaseModel):
    audio_url: str
    duration_sec: float


class STTRequest(BaseModel):
    audio_blob_path: str


class STTResponse(BaseModel):
    text: str
    confidence: float
