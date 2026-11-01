"""Dashboard response schemas (P7A-01).

Every block carries `available` + `updated_at`, and blocks that can fail
carry an explicit `unavailable_reason` — missing data is shown as missing,
never fabricated (master prompt §16; DEPENDENCY_POLICY rule 6).
"""

import datetime as dt

from pydantic import BaseModel, Field


class FarmBlock(BaseModel):
    available: bool = True
    updated_at: dt.datetime
    name: str
    timezone: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CropItem(BaseModel):
    crop: str
    status: str
    season_year: int
    planting_date: dt.date | None = None
    expected_harvest_date: dt.date | None = None


class CropsBlock(BaseModel):
    available: bool = True
    updated_at: dt.datetime
    cycles: list[CropItem] = Field(default_factory=list)
    unavailable_reason: str | None = None


class WeatherBlock(BaseModel):
    available: bool = False
    updated_at: dt.datetime
    temperature: float | None = None
    windspeed: float | None = None
    conditions: str | None = None
    unavailable_reason: str | None = None


class TaskItem(BaseModel):
    title: str
    due_date: dt.date
    crop: str


class TasksBlock(BaseModel):
    available: bool = True
    updated_at: dt.datetime
    items: list[TaskItem] = Field(default_factory=list)
    unavailable_reason: str | None = None


class AlertItem(BaseModel):
    severity: str = "info"
    message: str


class AlertsBlock(BaseModel):
    available: bool = True
    updated_at: dt.datetime
    items: list[AlertItem] = Field(default_factory=list)


class RecommendationsBlock(BaseModel):
    # Explicit: the saved-recommendation feature does not exist yet. Shown as
    # an honest empty state — never fabricated.
    available: bool = False
    unavailable_reason: str = "Saved recommendations are not available yet"


class ActivityItem(BaseModel):
    event_type: str
    description: str | None = None
    occurred_at: dt.datetime


class ActivityBlock(BaseModel):
    available: bool = True
    updated_at: dt.datetime
    items: list[ActivityItem] = Field(default_factory=list)
    unavailable_reason: str | None = None


class DashboardResponse(BaseModel):
    farm_id: str
    generated_at: dt.datetime
    farm: FarmBlock
    crops: CropsBlock
    weather: WeatherBlock
    tasks: TasksBlock
    alerts: AlertsBlock
    recommendations: RecommendationsBlock
    activity: ActivityBlock
