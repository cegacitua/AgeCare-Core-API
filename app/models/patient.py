from datetime import date, datetime
from typing import Optional, List, Any
from sqlalchemy import String, Date, JSON, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import ModelMixin


class Patient(Base, ModelMixin):
    __tablename__ = "patients"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    conditions: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)  # List of strings/dicts
    timezone: Mapped[str] = mapped_column(String(50), default="America/Santiago", nullable=False)

    # Relationships
    members: Mapped[List["PatientMember"]] = relationship("PatientMember", back_populates="patient", cascade="all, delete-orphan")
    wearable: Mapped[Optional["Wearable"]] = relationship("Wearable", back_populates="patient", uselist=False, cascade="all, delete-orphan")


class PatientMember(Base, ModelMixin):
    __tablename__ = "patient_members"
    __table_args__ = (
        UniqueConstraint("patient_id", "user_id", name="uq_patient_user"),
    )

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # family | caregiver | doctor | elder
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="patient_memberships")


class Invitation(Base, ModelMixin):
    __tablename__ = "invitations"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class Wearable(Base, ModelMixin):
    __tablename__ = "wearables"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    battery_pct: Mapped[int] = mapped_column(default=100, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="wearable")
