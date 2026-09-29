from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class Photo(Base, ModelMixin):
    __tablename__ = "photos"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    upload_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    shared_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class PhotoReaction(Base, ModelMixin):
    __tablename__ = "photo_reactions"
    __table_args__ = (
        UniqueConstraint("photo_id", "user_id", "kind", name="uq_photo_user_reaction_kind"),
    )

    photo_id: Mapped[str] = mapped_column(String(36), ForeignKey("photos.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # heart | voice
    voice_blob_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class ContentItem(Base, ModelMixin):
    __tablename__ = "content_items"

    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # joke | news
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(4000), nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audio_blob_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="es-CL", nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
