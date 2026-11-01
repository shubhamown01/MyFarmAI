"""Dashboard aggregation service (P7A-01).

Read-only, user-scoped assembly of the farm intelligence dashboard from
existing sources. Each block degrades independently: an unavailable source
never blanks the dashboard and never crashes the request. No model calls,
no invented statistics — only data that exists in the owner's database or
the optional weather provider (fail-open per DEPENDENCY_POLICY rule 6/15).
"""

import datetime as dt
import logging

from sqlalchemy import select

from app.db.models.crop import Crop, CropCycle, CropCycleStatus
from app.db.repositories import AuditRepository
from app.schemas.dashboard import (
    ActivityBlock,
    ActivityItem,
    AlertItem,
    AlertsBlock,
    CropItem,
    CropsBlock,
    DashboardResponse,
    FarmBlock,
    RecommendationsBlock,
    TaskItem,
    TasksBlock,
    WeatherBlock,
)
from app.services.context import FarmContextService
from app.services.farm import FarmService
from app.services.weather import weather_client

logger = logging.getLogger("myfarmai.dashboard")

_ACTIVE_STATUSES = (
    CropCycleStatus.PLANNED,
    CropCycleStatus.PLANTED,
    CropCycleStatus.GROWING,
)


class DashboardService:
    """Read-only farm dashboard assembly for authorized farm members."""

    def __init__(self, session, farm_service: FarmService):
        self._session = session
        self._farm_service = farm_service
        self._context = FarmContextService(session, farm_service)

    async def get_dashboard(self, user_id: str, farm_id: str) -> DashboardResponse:
        # Authorization happens inside get_context (member roles incl. VIEWER).
        # Raises FarmNotFoundError for non-members (no existence leak).
        ctx = await self._context.get_context(user_id, farm_id)
        now = dt.datetime.now(dt.UTC)

        # --- Crops block: active cycles joined to crop names (existing data).
        rows = (
            await self._session.execute(
                select(
                    Crop.name,
                    CropCycle.status,
                    CropCycle.season_year,
                    CropCycle.planting_date,
                    CropCycle.expected_harvest_date,
                )
                .join(Crop, Crop.id == CropCycle.crop_id)
                .where(CropCycle.farm_id == farm_id, CropCycle.status.in_(_ACTIVE_STATUSES))
                .order_by(CropCycle.expected_harvest_date.asc().nullslast())
            )
        ).all()
        crop_items = [
            CropItem(
                crop=name,
                status=status.value,
                season_year=season_year,
                planting_date=planting_date,
                expected_harvest_date=harvest_date,
            )
            for name, status, season_year, planting_date, harvest_date in rows
        ]
        crops_block = CropsBlock(available=True, updated_at=now, cycles=crop_items)

        # --- Weather block: OPTIONAL-FREE-EXTERNAL, fail-open.
        if ctx.latitude is None or ctx.longitude is None:
            weather_block = WeatherBlock(
                updated_at=now, unavailable_reason="Farm has no coordinates set"
            )
        else:
            try:
                data = await weather_client.get_weather(
                    float(ctx.latitude), float(ctx.longitude), include_daily=False
                )
                cw = data.get("current_weather") or {}
                weather_block = WeatherBlock(
                    available=True,
                    updated_at=now,
                    temperature=cw.get("temperature"),
                    windspeed=cw.get("windspeed"),
                    conditions=cw.get("weather_description"),
                )
            except Exception:
                # Fail-open: a weather outage must never block the dashboard.
                logger.warning("Weather unavailable for dashboard (farm %s)", farm_id)
                weather_block = WeatherBlock(
                    updated_at=now, unavailable_reason="Weather service unavailable"
                )

        # --- Tasks block: upcoming expected-harvest windows only (existing
        # dates; nothing predicted or invented).
        today = dt.date.today()
        task_items = [
            TaskItem(
                title="Expected harvest window",
                due_date=c.expected_harvest_date,
                crop=c.crop,
            )
            for c in crop_items
            if c.expected_harvest_date is not None and today <= c.expected_harvest_date
        ]
        tasks_block = TasksBlock(updated_at=now, items=task_items)

        # --- Alerts block: derived locally from real state only.
        alert_items: list[AlertItem] = []
        if not weather_block.available:
            alert_items.append(
                AlertItem(message=f"Weather unavailable: {weather_block.unavailable_reason}")
            )
        if not crop_items:
            alert_items.append(AlertItem(message="No active crop cycles on this farm yet"))
        for c in crop_items:
            if c.expected_harvest_date is not None and c.expected_harvest_date < today:
                alert_items.append(
                    AlertItem(
                        severity="warning",
                        message=f"{c.crop} harvest window passed ({c.expected_harvest_date}) — update the cycle status",
                    )
                )
        alerts_block = AlertsBlock(updated_at=now, items=alert_items)

        # --- Activity block: the user's own recent audit events (privacy:
        # never another user's events).
        events = await AuditRepository(self._session).get_user_events(user_id, limit=20)
        activity_block = ActivityBlock(
            updated_at=now,
            items=[
                ActivityItem(
                    event_type=e.event_type.value,
                    description=e.description,
                    occurred_at=e.occurred_at,
                )
                for e in events
            ],
        )

        return DashboardResponse(
            farm_id=str(ctx.farm_id),
            generated_at=now,
            farm=FarmBlock(
                available=True,
                updated_at=now,
                name=ctx.name,
                timezone=ctx.timezone,
                address=ctx.address,
                latitude=ctx.latitude,
                longitude=ctx.longitude,
            ),
            crops=crops_block,
            weather=weather_block,
            tasks=tasks_block,
            alerts=alerts_block,
            recommendations=RecommendationsBlock(),
            activity=activity_block,
        )
