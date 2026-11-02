"""Crop catalogue and crop cycle models."""

import uuid
from datetime import date, datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.farm import Farm
    from app.db.models.conversation import Conversation


class CropCategory(str, PyEnum):
    """Crop categories."""

    CEREAL = "cereal"
    PULSE = "pulse"
    OILSEED = "oilseed"
    FIBER = "fiber"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    SPICE = "spice"
    FODDER = "fodder"
    OTHER = "other"


class Crop(Base, TimestampMixin, UUIDMixin):
    """Crop catalogue - reference data for crop types."""

    __tablename__ = "crops"

    # Identity
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    scientific_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[CropCategory] = mapped_column(
        SQLEnum(CropCategory, native_enum=False),
        default=CropCategory.OTHER,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Growing parameters (reference values)
    min_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimal_rainfall_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    growing_days_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    growing_days_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    crop_cycles: Mapped[list["CropCycle"]] = relationship(
        "CropCycle",
        back_populates="crop",
    )

    __table_args__ = (
        Index("ix_crops_category_active", "category", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Crop(id={self.id}, name={self.name}, category={self.category})>"


class CropCycleStatus(str, PyEnum):
    """Crop cycle status."""

    PLANNED = "planned"
    PLANTED = "planted"
    GROWING = "growing"
    HARVESTED = "harvested"
    FAILED = "failed"
    ARCHIVED = "archived"


class CropCycle(Base, TimestampMixin, UUIDMixin):
    """Crop cycle - a specific crop growing season on a farm."""

    __tablename__ = "crop_cycles"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Season info
    season_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    season_year: Mapped[int] = mapped_column(nullable=False)

    # Dates
    planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Area
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_acres: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status and yield
    status: Mapped[CropCycleStatus] = mapped_column(
        SQLEnum(CropCycleStatus, native_enum=False),
        default=CropCycleStatus.PLANNED,
        nullable=False,
    )
    expected_yield_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_yield_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_unit: Mapped[str] = mapped_column(String(20), default="kg/ha", nullable=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="crop_cycles",
    )
    crop: Mapped["Crop"] = relationship(
        "Crop",
        back_populates="crop_cycles",
    )

    __table_args__ = (
        Index("ix_crop_cycles_farm_status", "farm_id", "status"),
        Index("ix_crop_cycles_farm_year", "farm_id", "season_year"),
        UniqueConstraint("farm_id", "crop_id", "season_year", name="uq_farm_crop_season"),
    )

    def __repr__(self) -> str:
        return f"<CropCycle(id={self.id}, farm_id={self.farm_id}, crop_id={self.crop_id}, status={self.status})>"