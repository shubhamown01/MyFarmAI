"""Crop-plan API schemas (P7B)."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.crop_plan import CropPlanTaskSource, CropPlanTaskStatus


class PlanTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    due_date: date | None = None


class PlanTaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    due_date: date | None = None
    status: CropPlanTaskStatus | None = None


class PlanTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    due_date: date | None
    source: CropPlanTaskSource
    status: CropPlanTaskStatus
    created_at: datetime


class PlanTaskStatusResponse(PlanTaskResponse):
    plan_id: uuid.UUID


class MilestoneResponse(BaseModel):
    title: str
    date: date
    note: str | None = None


class CropPlanCreate(BaseModel):
    crop_cycle_id: uuid.UUID | None = None
    variety: str | None = Field(None, max_length=100)
    planting_date: date | None = None
    tasks: list[PlanTaskCreate] = []


class CropPlanUpdate(BaseModel):
    crop_cycle_id: uuid.UUID | None = None
    variety: str | None = Field(None, max_length=100)
    planting_date: date | None = None


class CropPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    user_id: uuid.UUID
    crop_cycle_id: uuid.UUID | None
    variety: str | None
    planting_date: date | None
    assumptions: str | None
    milestones: list[MilestoneResponse]
    tasks: list[PlanTaskResponse]
    created_at: datetime
    updated_at: datetime


class CropPlanRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    changed_by: uuid.UUID
    summary: str
    snapshot: dict[str, Any]
    created_at: datetime
