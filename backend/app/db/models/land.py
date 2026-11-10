"""Farm land registration models (E4): plots, boundaries, area measurements, home locations."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.farm import Farm

# Land type values (CHECK-constrained in DB).
LAND_TYPES = ("home_farming", "small_outdoor", "agricultural", "other")
# Boundary source values.
BOUNDARY_SOURCES = ("map_drawn", "manual_entry")
# Measurement source values.
MEASUREMENT_SOURCES = ("map_measured", "user_reported")
# Home location source values.
HOME_LOCATION_SOURCES = ("auto_detected", "manual_entry", "map_pin")


class HomeLocation(Base, TimestampMixin, UUIDMixin):
    """Farmer's home location — separate from farm land (E4).

    A farmer may have a home location distinct from their farm(s).
    Never automatically assume the farmer lives on their farmland.
    """

    __tablename__ = "home_locations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g., "Home", "Primary residence"
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # auto_detected | manual_entry | map_pin
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "source IN ('auto_detected', 'manual_entry', 'map_pin')",
            name="ck_home_locations_source",
        ),
        Index("ix_home_locations_user_primary", "user_id", "is_primary"),
    )

    def __repr__(self) -> str:
        return f"<HomeLocation(user_id={self.user_id}, name={self.name})>"


class FarmPlot(Base, TimestampMixin, UUIDMixin):
    """A named land plot within a farm (E4)."""

    __tablename__ = "farm_plots"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    land_type: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    farm: Mapped["Farm"] = relationship("Farm", viewonly=True)  # noqa: F821
    boundary: Mapped["FarmBoundary | None"] = relationship(
        back_populates="plot",
        cascade="all, delete-orphan",
        uselist=False,
    )
    area_measurements: Mapped[list["FarmAreaMeasurement"]] = relationship(
        back_populates="plot",
        cascade="all, delete-orphan",
        order_by="FarmAreaMeasurement.created_at.desc()",
    )

    __table_args__ = (
        CheckConstraint(
            "land_type IN ('home_farming', 'small_outdoor', 'agricultural', 'other')",
            name="ck_farm_plots_land_type",
        ),
        Index("ix_farm_plots_farm_name", "farm_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<FarmPlot(id={self.id}, farm_id={self.farm_id}, name={self.name})>"


class FarmBoundary(Base, UUIDMixin):
    """The current (active) drawn boundary of a plot — one per plot.

    History is preserved via FarmAreaMeasurement rows; this row holds only
    the latest drawn polygon. No PostGIS: polygon is a JSON list of
    {lat, lon} objects (portable across dialects).
    """

    __tablename__ = "farm_boundaries"

    plot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    polygon: Mapped[list[dict[str, float]]] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    point_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    plot: Mapped["FarmPlot"] = relationship(back_populates="boundary")

    __table_args__ = (
        CheckConstraint(
            "source IN ('map_drawn', 'manual_entry')",
            name="ck_farm_boundaries_source",
        ),
    )

    def __repr__(self) -> str:
        return f"<FarmBoundary(plot_id={self.plot_id}, points={self.point_count})>"


class FarmAreaMeasurement(Base, UUIDMixin):
    """An area measurement event for a plot (history is append-only)."""

    __tablename__ = "farm_area_measurements"

    plot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farm_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    area_sq_m: Mapped[float] = mapped_column(Float, nullable=False)
    area_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    user_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    plot: Mapped["FarmPlot"] = relationship(back_populates="area_measurements")

    __table_args__ = (
        CheckConstraint(
            "source IN ('map_measured', 'user_reported')",
            name="ck_farm_area_measurements_source",
        ),
        CheckConstraint(
            "area_unit IN ('sq_m', 'sq_km', 'hectare', 'acre', 'sq_ft', 'sq_yd')",
            name="ck_farm_area_measurements_unit",
        ),
        Index("ix_farm_area_measurements_plot_created", "plot_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<FarmAreaMeasurement(plot_id={self.plot_id}, area_sq_m={self.area_sq_m})>"
