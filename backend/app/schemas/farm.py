"""Farm API schemas (P5A-01)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.farm import FarmRole


class FarmCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    address: str | None = Field(None, max_length=500)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    timezone: str = Field("UTC", max_length=50)


class FarmUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    address: str | None = Field(None, max_length=500)
    latitude: float | None = Field(None, ge=-90.0, le=90.0)
    longitude: float | None = Field(None, ge=-180.0, le=180.0)
    timezone: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    address: str | None
    latitude: float | None
    longitude: float | None
    timezone: str
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime


class FarmMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: FarmRole = FarmRole.MEMBER

    @field_validator("role")
    @classmethod
    def role_not_owner(cls, v: FarmRole) -> FarmRole:
        if v == FarmRole.OWNER:
            raise ValueError("ownership is fixed to the farm creator")
        return v


class FarmMemberRoleUpdate(BaseModel):
    role: FarmRole

    @field_validator("role")
    @classmethod
    def role_not_owner(cls, v: FarmRole) -> FarmRole:
        if v == FarmRole.OWNER:
            raise ValueError("cannot grant ownership via role update")
        return v


class FarmMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role: FarmRole
    joined_at: datetime
