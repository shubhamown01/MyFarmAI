"""Crop-cycle service (P5A-02): farm-scoped authorization over CropCycleRepository.

Authorization (same model as FarmService, ADR-008 404 semantics):
- Non-members get not-found for anything under the farm.
- VIEWER is read-only; create/update require MEMBER or OWNER.

CropCycleRepository has no update method; this service mutates the ORM object
directly (farm-scoped authz happens here first).

No CROP_CYCLE_* audit event types exist yet (owner decision pending) — cycles
are intentionally not audit-logged in this iteration.
"""

from sqlalchemy.exc import IntegrityError

from app.db.models.crop import CropCycle, CropCycleStatus
from app.db.models.farm import FarmRole
from app.db.repositories import CropCycleRepository, CropRepository


class CropCycleNotFoundError(Exception):
    pass


class CropCycleConflictError(Exception):
    """Unique-constraint violation: (farm, crop, season) already exists."""


class CropCycleStatusError(Exception):
    """Invalid status transition."""


class CropNotFoundError(Exception):
    pass


# Forward-only lifecycle; archived is terminal.
_ALLOWED_TRANSITIONS: dict[CropCycleStatus, set[CropCycleStatus]] = {
    CropCycleStatus.PLANNED: {
        CropCycleStatus.PLANTED,
        CropCycleStatus.FAILED,
        CropCycleStatus.ARCHIVED,
    },
    CropCycleStatus.PLANTED: {
        CropCycleStatus.GROWING,
        CropCycleStatus.FAILED,
        CropCycleStatus.ARCHIVED,
    },
    CropCycleStatus.GROWING: {
        CropCycleStatus.HARVESTED,
        CropCycleStatus.FAILED,
        CropCycleStatus.ARCHIVED,
    },
    CropCycleStatus.HARVESTED: {CropCycleStatus.ARCHIVED},
    CropCycleStatus.FAILED: {CropCycleStatus.ARCHIVED},
    CropCycleStatus.ARCHIVED: set(),
}

_ALL_ROLES = (FarmRole.OWNER, FarmRole.MEMBER, FarmRole.VIEWER)
_WRITE_ROLES = (FarmRole.OWNER, FarmRole.MEMBER)


class CropCycleService:
    """Crop-cycle CRUD with farm-scoped authorization."""

    def __init__(self, session, farm_service):
        self._cycles = CropCycleRepository(session)
        self._crops = CropRepository(session)
        self._farm_service = farm_service  # provides _authorized_farm

    async def _authorized_cycle(
        self, user_id: str, cycle_id: str, *, require_member: bool = False
    ) -> CropCycle:
        cycle = await self._cycles.get_by_id(cycle_id)
        if not cycle:
            raise CropCycleNotFoundError(cycle_id)
        await self._farm_service._authorized_farm(
            user_id, str(cycle.farm_id), require=_WRITE_ROLES if require_member else _ALL_ROLES
        )
        return cycle

    async def create_cycle(self, user_id: str, farm_id: str, **kwargs) -> CropCycle:
        await self._farm_service._authorized_farm(user_id, farm_id, require=_WRITE_ROLES)
        crop_id = str(kwargs["crop_id"])
        if not await self._crops.get_by_id(crop_id):
            raise CropNotFoundError(crop_id)
        try:
            return await self._cycles.create(farm_id=farm_id, **kwargs)
        except IntegrityError as e:
            raise CropCycleConflictError(
                "a cycle for this crop and season already exists on the farm"
            ) from e

    async def list_cycles(
        self, user_id: str, farm_id: str, status: CropCycleStatus | None = None
    ) -> list[CropCycle]:
        await self._farm_service._authorized_farm(user_id, farm_id, require=_ALL_ROLES)
        return list(await self._cycles.list_by_farm(farm_id, status))

    async def get_cycle(self, user_id: str, cycle_id: str) -> CropCycle:
        return await self._authorized_cycle(user_id, cycle_id)

    async def update_cycle(self, user_id: str, cycle_id: str, **kwargs) -> CropCycle:
        cycle = await self._authorized_cycle(user_id, cycle_id, require_member=True)
        new_status = kwargs.get("status")
        if (
            new_status is not None
            and new_status != cycle.status
            and new_status not in _ALLOWED_TRANSITIONS[cycle.status]
        ):
            raise CropCycleStatusError(
                f"cannot move cycle from '{cycle.status.value}' to '{new_status.value}'"
            )
        for key, value in kwargs.items():
            setattr(cycle, key, value)
        return cycle
