"""Land registration API schemas (E4): plots, boundaries, measurements, home location.

Area units are CHECK-constrained in the DB and validated here. Polygons are
lists of {lat, lon} points (NO PostGIS, owner-approved) — area is computed
server-side with the geodesic spherical-excess formula in
``app.services.geometry``.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

LandType = Literal["home_farming", "small_outdoor", "agricultural", "other"]
AreaUnit = Literal["sq_m", "sq_km", "hectare", "acre", "sq_ft", "sq_yd"]


class PolygonPoint(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class PlotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    land_type: LandType
    notes: str | None = Field(None, max_length=1000)


class PlotUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    land_type: LandType | None = None
    notes: str | None = Field(None, max_length=1000)


class BoundarySave(BaseModel):
    """Replace the plot's (single) boundary. Source distinguishes a
    map-drawn polygon from coordinates the farmer typed manually."""

    polygon: list[PolygonPoint] = Field(..., min_length=3, max_length=500)
    source: Literal["map_drawn", "manual_entry"]


class BoundaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    polygon: list[PolygonPoint]
    source: str
    point_count: int
    created_at: datetime


class AreaMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plot_id: UUID
    area_sq_m: float
    area_unit: str
    source: str
    user_confirmed: bool
    calculated_at: datetime
    # The same area expressed in every supported unit (directive §7.4).
    conversions: dict[str, float]


class PlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    farm_id: UUID
    name: str
    land_type: str
    notes: str | None
    boundary: BoundaryResponse | None = None
    latest_measurement: AreaMeasurementResponse | None = None
    created_at: datetime
    updated_at: datetime


class UserReportedArea(BaseModel):
    """Manual area entry (directive §7.3): recorded as user_reported, never
    presented as map-measured. Optionally marks it farmer-confirmed."""

    area_value: float = Field(..., gt=0.0, le=1_000_000_000.0)
    area_unit: AreaUnit
    confirm: bool = False


class HomeLocationSave(BaseModel):
    """Upsert of the farmer's home location (one per user)."""

    name: str = Field("Home", min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy_m: float | None = Field(None, ge=0.0)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    district: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    source: Literal["auto_detected", "manual_entry", "map_pin"]


class HomeLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    latitude: float
    longitude: float
    accuracy_m: float | None
    address: str | None
    city: str | None
    district: str | None
    state: str | None
    country: str | None
    postal_code: str | None
    source: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime
