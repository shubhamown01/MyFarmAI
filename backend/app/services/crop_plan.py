"""Crop-plan service (P7B): farmer-controlled planning with change history.

Authorization follows FarmService (ADR-008 404 semantics): non-members get
not-found; VIEWER is read-only. Every plan mutation appends an immutable
revision with a snapshot of the plan before the change. Farmer decisions are
never silently overwritten: tasks created via the API are always `user`
sourced (the system never edits or deletes them; cancellation is soft).

Milestones derive ONLY from planting_date + Crop.growing_days_min/max (local
computation, zero external APIs) and their assumptions are displayed
verbatim. No fertilizer/chemical quantities exist anywhere in this service.
"""

from datetime import date, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.crop_plan import (
    CropPlan,
    CropPlanRevision,
    CropPlanTask,
    CropPlanTaskSource,
    CropPlanTaskStatus,
)
from app.db.models.farm import FarmRole
from app.db.repositories import (
    CropCycleRepository,
    CropPlanRepository,
    CropRepository,
)
from app.services.farm import FarmService

ASSUMPTIONS_TEXT = (
    "Milestones are estimates from generic growing-day ranges for the crop — "
    "variety, local climate and soil are not accounted for unless data exists."
)

_ALL_ROLES = (FarmRole.OWNER, FarmRole.MEMBER, FarmRole.VIEWER)
_WRITE_ROLES = (FarmRole.OWNER, FarmRole.MEMBER)


class CropPlanNotFoundError(Exception):
    pass


class CropPlanInvalidError(Exception):
    """Invalid plan reference (e.g. cycle not on this farm)."""


class PlanTaskNotFoundError(Exception):
    pass


class CropPlanService:
    """Crop-plan CRUD + task lifecycle + milestone derivation."""

    def __init__(self, session: AsyncSession, farm_service: FarmService) -> None:
        self._plans = CropPlanRepository(session)
        self._cycles = CropCycleRepository(session)
        self._crops = CropRepository(session)
        self._farm_service = farm_service  # provides _authorized_farm

    # --- milestones -------------------------------------------------------

    async def _milestones(self, plan: CropPlan) -> list[dict[str, Any]]:
        """Derive milestones from planting_date + generic growing-day ranges.

        No data, no milestones — never invented. Assumptions ride along.
        """
        if not plan.planting_date or not plan.crop_cycle_id:
            return []
        cycle = await self._cycles.get_by_id(str(plan.crop_cycle_id))
        if not cycle:
            return []
        crop = await self._crops.get_by_id(str(cycle.crop_id))
        if not crop or not crop.growing_days_min and not crop.growing_days_max:
            return []
        milestones = [{"title": "Sowing / planting", "date": plan.planting_date, "note": None}]
        if crop.growing_days_min:
            milestones.append(
                {
                    "title": "Expected harvest (earliest)",
                    "date": plan.planting_date + timedelta(days=crop.growing_days_min),
                    "note": f"~{crop.growing_days_min} growing days",
                }
            )
        if crop.growing_days_max:
            milestones.append(
                {
                    "title": "Expected harvest (latest)",
                    "date": plan.planting_date + timedelta(days=crop.growing_days_max),
                    "note": f"~{crop.growing_days_max} growing days",
                }
            )
        return milestones

    # --- revisions --------------------------------------------------------

    @staticmethod
    def _snapshot(plan: CropPlan) -> dict[str, Any]:
        return {
            "variety": plan.variety,
            "planting_date": plan.planting_date.isoformat() if plan.planting_date else None,
            "crop_cycle_id": str(plan.crop_cycle_id) if plan.crop_cycle_id else None,
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "source": t.source.value,
                    "status": t.status.value,
                }
                for t in plan.tasks
            ],
        }

    async def _record(self, plan: CropPlan, user_id: str, summary: str) -> None:  # noqa
        await self._plans.append_revision(str(plan.id), user_id, summary, self._snapshot(plan))

    # --- plan lifecycle ---------------------------------------------------

    async def create_plan(self, user_id: str, farm_id: str, **kwargs: Any) -> CropPlan:
        await self._farm_service._authorized_farm(user_id, farm_id, require=_WRITE_ROLES)
        tasks = kwargs.pop("tasks", [])
        cycle_id = kwargs.pop("crop_cycle_id", None)
        if cycle_id:
            cycle = await self._cycles.get_by_id(str(cycle_id))
            if not cycle or str(cycle.farm_id) != str(farm_id):
                raise CropPlanInvalidError("crop cycle does not belong to this farm")
        plan = await self._plans.create(
            user_id, farm_id, crop_cycle_id=cycle_id, tasks=tasks, **kwargs
        )
        await self._plans.get_by_id(str(plan.id))  # load tasks for the snapshot
        await self._record(plan, user_id, "plan created")
        return plan

    async def list_plans(self, user_id: str, farm_id: str) -> list[CropPlan]:
        await self._farm_service._authorized_farm(user_id, farm_id, require=_ALL_ROLES)
        return list(await self._plans.list_by_farm(farm_id))

    async def get_plan(self, user_id: str, plan_id: str) -> CropPlan:
        return await self._authorized_plan(user_id, plan_id)

    async def update_plan(self, user_id: str, plan_id: str, **fields: Any) -> CropPlan:
        plan = await self._authorized_plan(user_id, plan_id, require_member=True)
        cycle_id = fields.pop("crop_cycle_id", None)
        changed = list(fields)
        if cycle_id is not None:
            cycle = await self._cycles.get_by_id(str(cycle_id))
            if not cycle or str(cycle.farm_id) != str(plan.farm_id):
                raise CropPlanInvalidError("crop cycle does not belong to this farm")
        await self._record(
            plan,
            user_id,
            f"updated: {', '.join(changed) or 'no fields'}" if changed else "plan updated",
        )
        if cycle_id is not None:
            plan.crop_cycle_id = cycle_id
        for key, value in fields.items():
            setattr(plan, key, value)
        return plan

    async def get_revisions(self, user_id: str, plan_id: str) -> list[CropPlanRevision]:
        plan = await self._authorized_plan(user_id, plan_id)
        return sorted(plan.revisions, key=lambda r: r.created_at)

    # --- task lifecycle ---------------------------------------------------

    async def add_task(
        self, user_id: str, plan_id: str, title: str, due_date: date | None = None
    ) -> CropPlanTask:
        plan = await self._authorized_plan(user_id, plan_id, require_member=True)
        task = CropPlanTask(
            plan_id=plan.id,
            title=title,
            due_date=due_date,
            source=CropPlanTaskSource.USER,
            status=CropPlanTaskStatus.PENDING,  # explicit: column defaults apply at flush
        )
        plan.tasks.append(task)
        await self._record(plan, user_id, f"task added: {title}")
        return task

    async def update_task(
        self, user_id: str, plan_id: str, task_id: str, **fields: Any
    ) -> CropPlanTask:
        """User tasks are freely editable by the farmer (never by the system);
        `source` is immutable. Cancellation is soft — nothing is hard-deleted."""
        plan = await self._authorized_plan(user_id, plan_id, require_member=True)
        task = next((t for t in plan.tasks if str(t.id) == task_id), None)
        if not task:
            raise PlanTaskNotFoundError(task_id)
        fields.pop("source", None)  # farmer decisions are never re-attributed
        await self._record(plan, user_id, f"task updated (before change): {task.title}")
        for key, value in fields.items():
            if value is not None:
                setattr(task, key, value)
        return task

    # --- helpers ----------------------------------------------------------

    async def _authorized_plan(
        self, user_id: str, plan_id: str, *, require_member: bool = False
    ) -> CropPlan:
        plan = await self._plans.get_by_id(plan_id)
        if not plan:
            raise CropPlanNotFoundError(plan_id)
        await self._farm_service._authorized_farm(
            user_id, str(plan.farm_id), require=_WRITE_ROLES if require_member else _ALL_ROLES
        )
        return plan
