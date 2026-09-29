from typing import Optional, Any
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import ModelMixin


class MarketplaceProduct(Base, ModelMixin):
    __tablename__ = "marketplace_products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # mobility | hygiene | safety | comfort | tech
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    photos: Mapped[Optional[Any]] = mapped_column(JSON, default=list, nullable=True)
    price_range: Mapped[str] = mapped_column(String(100), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_info: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CaregiverReview(Base, ModelMixin):
    __tablename__ = "caregiver_reviews"
    __table_args__ = (
        UniqueConstraint("profile_id", "author_id", name="uq_caregiver_author_review"),
    )

    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("caregiver_profiles.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    comment: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)


class ContactRequest(Base, ModelMixin):
    __tablename__ = "contact_requests"

    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("caregiver_profiles.id", ondelete="CASCADE"), nullable=False)
    family_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
