from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class Alert(Base, ModelMixin):
    __tablename__ = "alerts"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # fall | vital_out_of_range | missed_dose | sos | wearable_offline
    severity: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)  # info | warning | critical
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(String(1000), nullable=False)
    payload: Mapped[Optional[Any]] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | acknowledged | resolved
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)


class NotificationSetting(Base, ModelMixin):
    __tablename__ = "notification_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "alert_type", name="uq_user_alert_setting"),
    )

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SOSEvent(Base, ModelMixin):
    __tablename__ = "sos_events"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    alert_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
