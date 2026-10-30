"""Farm context assembly (P5A-03): read-only resolver for prompt grounding.

Given an authorized farm member, resolves the structured farm/crop context
that P5B will feed into the system prompt. Missing fields stay None/[]
(unknown) — never fabricated.

Privacy (P5A-04): coordinates/address are returned ONLY to farm members;
callers must never log them. Retention follows ADR-015 (owner-pending).
"""

from dataclasses import dataclass, field

from sqlalchemy import select

from app.db.models.crop import Crop, CropCycle, CropCycleStatus
from app.db.models.farm import FarmRole


@dataclass
class FarmContext:
    """Authorized farm context. Coordinates must never be logged."""

    farm_id: str
    name: str
    timezone: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    active_crops: list[str] = field(default_factory=list)


_ACTIVE_STATUSES = (
    CropCycleStatus.PLANNED,
    CropCycleStatus.PLANTED,
    CropCycleStatus.GROWING,
)


class FarmContextService:
    """Read-only farm context for authorized farm members."""

    def __init__(self, session, farm_service):
        self._session = session
        self._farm_service = farm_service  # provides _authorized_farm

    async def get_context(self, user_id: str, farm_id: str) -> FarmContext:
        farm = await self._farm_service._authorized_farm(
            user_id,
            farm_id,
            require=(
                FarmRole.OWNER,
                FarmRole.MEMBER,
                FarmRole.VIEWER,
            ),
        )
        result = await self._session.execute(
            select(Crop.name)
            .join(CropCycle, CropCycle.crop_id == Crop.id)
            .where(CropCycle.farm_id == farm_id)
            .where(CropCycle.status.in_(_ACTIVE_STATUSES))
            .distinct()
            .order_by(Crop.name)
        )
        return FarmContext(
            farm_id=str(farm.id),
            name=farm.name,
            timezone=farm.timezone,
            address=farm.address,
            latitude=farm.latitude,
            longitude=farm.longitude,
            active_crops=[row[0] for row in result.all()],
        )
