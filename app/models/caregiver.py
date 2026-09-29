from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, Boolean, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class CareTask(Base, ModelMixin):
    __tablename__ = "care_tasks"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="hygiene", nullable=False)  # hygiene | food | exercise | medical | custom
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recurrence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # daily | weekly | once
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending | done | skipped
    done_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    task_date: Mapped[date] = mapped_column(Date, nullable=False)


class CaregiverProfile(Base, ModelMixin):
    __tablename__ = "caregiver_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str] = mapped_column(String(2000), nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specialties: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)
    languages: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)
    zones: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)
    certifications: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)
    is_listed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CaregiverSubscription(Base, ModelMixin):
    __tablename__ = "caregiver_subscriptions"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)  # free | premium
    store: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # app_store | play_store | web
    purchase_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JobOffer(Base, ModelMixin):
    __tablename__ = "job_offers"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    zone: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule: Mapped[str] = mapped_column(String(100), nullable=False)
    pay_range: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_info: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
