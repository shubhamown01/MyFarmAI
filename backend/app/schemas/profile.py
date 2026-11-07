"""Farmer profile + onboarding API schemas (E5)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FarmingType = Literal["home_farming", "small_outdoor", "agricultural", "other"]


class FarmerProfileUpdate(BaseModel):
    """Progressive profile: every field optional, upsert semantics."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    farming_type: FarmingType | None = None
    preferred_language: str | None = Field(None, min_length=2, max_length=10)
    farming_experience_years: int | None = Field(None, ge=0, le=100)
    existing_crops: list[str] | None = Field(None, max_length=50)
    intended_crops: list[str] | None = Field(None, max_length=50)
    soil_info: str | None = Field(None, max_length=500)
    water_availability: str | None = Field(None, max_length=100)
    growing_season: str | None = Field(None, max_length=100)

    @field_validator("existing_crops", "intended_crops")
    @classmethod
    def crop_names_valid(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for name in v:
                if not (0 < len(name.strip()) <= 100):
                    raise ValueError("each crop name must be 1-100 characters")
        return [name.strip() for name in v] if v else v


class FarmerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None
    farming_type: str | None
    preferred_language: str | None
    farming_experience_years: int | None
    existing_crops: list[str] | None
    intended_crops: list[str] | None
    soil_info: str | None
    water_availability: str | None
    growing_season: str | None
    profile_completed: bool
    created_at: datetime
    updated_at: datetime


class OnboardingStep(BaseModel):
    step: str
    complete: bool
    detail: str | None = None


class OnboardingStatusResponse(BaseModel):
    """Computed onboarding state (directive §12: resume incomplete onboarding).

    No separate state table — the state is derived from existing records so
    it can never drift from the source of truth.
    """

    verification_status: str
    steps: list[OnboardingStep]
    next_step: str | None
    complete: bool
