"""Crop-cycle API schemas (P5A-02)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.crop import CropCycleStatus


class CropCycleCreate(BaseModel):
    crop_id: uuid.UUID
    season_year: int = Field(..., ge=1900, le=2100)
    season_name: str | None = Field(None, max_length=100)
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    area_hectares: float | None = Field(None, ge=0)
    area_acres: float | None = Field(None, ge=0)
    expected_yield_kg: float | None = Field(None, ge=0)
    yield_unit: str = Field("kg/ha", max_length=20)
    notes: str | None = Field(None, max_length=5000)


class CropCycleUpdate(BaseModel):
    season_name: str | None = Field(None, max_length=100)
    planting_date: date | None = None
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    area_hectares: float | None = Field(None, ge=0)
    area_acres: float | None = Field(None, ge=0)
    status: CropCycleStatus | None = None
    expected_yield_kg: float | None = Field(None, ge=0)
    actual_yield_kg: float | None = Field(None, ge=0)
    yield_unit: str | None = Field(None, max_length=20)
    notes: str | None = Field(None, max_length=5000)


class CropCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    crop_id: uuid.UUID
    season_name: str | None
    season_year: int
    planting_date: date | None
    expected_harvest_date: date | None
    actual_harvest_date: date | None
    area_hectares: float | None
    area_acres: float | None
    status: CropCycleStatus
    expected_yield_kg: float | None
    actual_yield_kg: float | None
    yield_unit: str
    notes: str | None
    created_at: datetime
