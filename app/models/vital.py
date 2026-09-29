from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class VitalReading(Base, ModelMixin):
    __tablename__ = "vital_readings"
    __table_args__ = (
        Index("idx_vital_patient_type_measured", "patient_id", "type", "measured_at"),
    )

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # heart_rate | spo2 | sleep | steps | sedentary_min | fall_event | blood_pressure | temperature | glucose
    value: Mapped[float] = mapped_column(Float, nullable=False)
    value_secondary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # e.g., diastolic for BP
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="wearable", nullable=False)  # wearable | manual
    meta: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)


class VitalThreshold(Base, ModelMixin):
    __tablename__ = "vital_thresholds"
    __table_args__ = (
        UniqueConstraint("patient_id", "type", name="uq_patient_vital_threshold"),
    )

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
