from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class Medication(Base, ModelMixin):
    __tablename__ = "medications"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dose: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "50mg"
    instructions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    times: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)  # list of times, e.g. ["08:00", "20:00"]
    days_of_week: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)  # [0,1,2,3,4,5,6]
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    grace_window_min: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    prescribed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    discontinued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ScheduledDose(Base, ModelMixin):
    __tablename__ = "scheduled_doses"

    medication_id: Mapped[str] = mapped_column(String(36), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | taken | postponed | missed
    logged_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    logged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    postponed_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
