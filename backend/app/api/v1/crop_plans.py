"""Crop-plan API endpoints (P7B)."""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.db.models.crop_plan import CropPlan
from app.db.session import db_manager
from app.schemas.crop_plan import (
    CropPlanCreate,
    CropPlanResponse,
    CropPlanRevisionResponse,
    CropPlanUpdate,
    MilestoneResponse,
    PlanTaskCreate,
    PlanTaskResponse,
    PlanTaskUpdate,
)
from app.services.crop_plan import (
    ASSUMPTIONS_TEXT,
    CropPlanInvalidError,
    CropPlanNotFoundError,
    CropPlanService,
    PlanTaskNotFoundError,
)
from app.services.farm import FarmNotFoundError, FarmPermissionError, FarmService

router = APIRouter(tags=["CropPlans"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_crop_plan_service(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[CropPlanService]:
    """CropPlanService bound to an async session that commits on clean completion."""
    async with db_manager.session() as session:
        yield CropPlanService(session, FarmService(session))


def _not_found(
    code: str = "CROP_PLAN_NOT_FOUND", detail: str = "crop plan not found"
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail={"detail": detail, "error_code": code}
    )


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
    )


def _invalid(e: CropPlanInvalidError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"detail": str(e), "error_code": "CROP_PLAN_INVALID"},
    )


async def _response(service: CropPlanService, plan: CropPlan) -> CropPlanResponse:
    milestones = await service._milestones(plan)
    return CropPlanResponse(
        id=plan.id,
        farm_id=plan.farm_id,
        user_id=plan.user_id,
        crop_cycle_id=plan.crop_cycle_id,
        variety=plan.variety,
        planting_date=plan.planting_date,
        assumptions=plan.assumptions or ASSUMPTIONS_TEXT,
        milestones=[MilestoneResponse(**m) for m in milestones],
        tasks=[PlanTaskResponse.model_validate(t) for t in plan.tasks],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post(
    "/farms/{farm_id}/crop-plans",
    response_model=CropPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    farm_id: uuid.UUID,
    data: CropPlanCreate,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropPlanResponse:
    try:
        plan = await service.create_plan(str(user_id), str(farm_id), **data.model_dump())
    except FarmNotFoundError:
        raise _not_found("FARM_NOT_FOUND", "farm not found") from None
    except FarmPermissionError:
        raise _forbidden() from None
    except CropPlanInvalidError as e:
        raise _invalid(e) from None
    return await _response(service, plan)


@router.get("/farms/{farm_id}/crop-plans", response_model=list[CropPlanResponse])
async def list_plans(
    farm_id: uuid.UUID,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[CropPlanResponse]:
    try:
        plans = await service.list_plans(str(user_id), str(farm_id))
    except FarmNotFoundError:
        raise _not_found("FARM_NOT_FOUND", "farm not found") from None
    return [await _response(service, p) for p in plans]


@router.get("/crop-plans/{plan_id}", response_model=CropPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropPlanResponse:
    try:
        plan = await service.get_plan(str(user_id), str(plan_id))
    except CropPlanNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    return await _response(service, plan)


@router.patch("/crop-plans/{plan_id}", response_model=CropPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: CropPlanUpdate,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropPlanResponse:
    try:
        plan = await service.update_plan(
            str(user_id), str(plan_id), **data.model_dump(exclude_unset=True)
        )
    except CropPlanNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    except FarmPermissionError:
        raise _forbidden() from None
    except CropPlanInvalidError as e:
        raise _invalid(e) from None
    return await _response(service, plan)


@router.get("/crop-plans/{plan_id}/revisions", response_model=list[CropPlanRevisionResponse])
async def list_revisions(
    plan_id: uuid.UUID,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[CropPlanRevisionResponse]:
    try:
        revisions = await service.get_revisions(str(user_id), str(plan_id))
    except CropPlanNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    return [CropPlanRevisionResponse.model_validate(r) for r in revisions]


@router.post(
    "/crop-plans/{plan_id}/tasks",
    response_model=PlanTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task(
    plan_id: uuid.UUID,
    data: PlanTaskCreate,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PlanTaskResponse:
    try:
        task = await service.add_task(str(user_id), str(plan_id), data.title, data.due_date)
    except CropPlanNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    except FarmPermissionError:
        raise _forbidden() from None
    return PlanTaskResponse.model_validate(task)


@router.patch("/crop-plans/{plan_id}/tasks/{task_id}", response_model=PlanTaskResponse)
async def update_task(
    plan_id: uuid.UUID,
    task_id: uuid.UUID,
    data: PlanTaskUpdate,
    service: CropPlanService = Depends(get_crop_plan_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PlanTaskResponse:
    try:
        task = await service.update_task(
            str(user_id), str(plan_id), str(task_id), **data.model_dump(exclude_unset=True)
        )
    except (CropPlanNotFoundError, PlanTaskNotFoundError):
        # task-not-found is indistinguishable from plan-not-found (no leak)
        raise _not_found(detail="crop plan or task not found") from None
    except FarmNotFoundError:
        raise _not_found() from None
    except FarmPermissionError:
        raise _forbidden() from None
    return PlanTaskResponse.model_validate(task)
