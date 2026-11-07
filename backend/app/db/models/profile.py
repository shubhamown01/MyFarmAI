"""Farmer profile (E5) — progressive agricultural personalization data.

All fields beyond ``full_name``/``farming_type`` are OPTIONAL (directive §8:
"Do not force farmers to provide information that is not required for core
onboarding"). ``profile_completed`` flips in code when the required fields
are present. No crops/area duplication here — farms, plots and measurements
live in their own tables and are linked via the onboarding state query.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User

# Aligned with land.py land types + a few specialized options (directive §7.2D).
FARMING_TYPES = (
    "home_farming",
    "small_outdoor",
    "agricultural",
    "other",
)


class FarmerProfile(Base, TimestampMixin, UUIDMixin):
    """One farmer profile per user."""

    __tablename__ = "farmer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    farming_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    farming_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    existing_crops: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    intended_crops: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    soil_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    water_availability: Mapped[str | None] = mapped_column(String(100), nullable=True)
    growing_season: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    user: Mapped["User"] = relationship("User", viewonly=True)

    __table_args__ = (
        CheckConstraint(
            "farming_type IN ('home_farming', 'small_outdoor', 'agricultural', 'other')",
            name="ck_farmer_profiles_farming_type",
        ),
        CheckConstraint(
            "farming_experience_years IS NULL OR (farming_experience_years >= 0 AND farming_experience_years <= 100)",
            name="ck_farmer_profiles_experience",
        ),
    )

    def __repr__(self) -> str:
        return f"<FarmerProfile(user_id={self.user_id}, profile_completed={self.profile_completed})>"
