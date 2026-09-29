from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class Observation(Base, ModelMixin):
    __tablename__ = "observations"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    photo_blob_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Incident(Base, ModelMixin):
    __tablename__ = "incidents"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)


class HandoverNote(Base, ModelMixin):
    __tablename__ = "handover_notes"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)


class ElderCheckin(Base, ModelMixin):
    __tablename__ = "elder_checkins"
    __table_args__ = (
        UniqueConstraint("patient_id", "date", name="uq_patient_elder_checkin_date"),
    )

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    feeling: Mapped[str] = mapped_column(String(50), nullable=False)  # happy | neutral | sad | in_pain
    date: Mapped[date] = mapped_column(Date, nullable=False)
