from typing import Optional, Any
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class VoiceNote(Base, ModelMixin):
    __tablename__ = "voice_notes"

    job_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    caregiver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processing", nullable=False)  # uploading | processing | completed | failed
    transcription_text: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # positive | neutral | negative
    extracted_data: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)
