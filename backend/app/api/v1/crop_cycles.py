"""Crop-cycle API endpoints (P5A-02)."""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.db.models.crop import CropCycleStatus
from app.db.session import db_manager
from app.schemas.crop_cycle import CropCycleCreate, CropCycleResponse, CropCycleUpdate
from app.services.crop_cycle import (
    CropCycleConflictError,
    CropCycleNotFoundError,
    CropCycleService,
    CropCycleStatusError,
    CropNotFoundError,
)
from app.services.farm import FarmNotFoundError, FarmPermissionError, FarmService

router = APIRouter(tags=["CropCycles"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_crop_cycle_service(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[CropCycleService]:
    """CropCycleService bound to an async session that commits on clean completion."""
    async with db_manager.session() as session:
        yield CropCycleService(session, FarmService(session))


def _not_found():
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"detail": "crop cycle not found", "error_code": "CROP_CYCLE_NOT_FOUND"},
    )


def _forbidden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
    )


@router.post(
    "/farms/{farm_id}/crop-cycles",
    response_model=CropCycleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cycle(
    farm_id: uuid.UUID,
    data: CropCycleCreate,
    service: CropCycleService = Depends(get_crop_cycle_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropCycleResponse:
    try:
        cycle = await service.create_cycle(str(user_id), str(farm_id), **data.model_dump())
    except FarmNotFoundError:
        raise _not_found() from None
    except FarmPermissionError:
        raise _forbidden() from None
    except CropNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "crop not found", "error_code": "CROP_NOT_FOUND"},
        ) from None
    except CropCycleConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": str(e), "error_code": "CROP_CYCLE_CONFLICT"},
        ) from None
    return CropCycleResponse.model_validate(cycle)


@router.get("/farms/{farm_id}/crop-cycles", response_model=list[CropCycleResponse])
async def list_cycles(
    farm_id: uuid.UUID,
    cycle_status: CropCycleStatus | None = Query(None, alias="status"),
    service: CropCycleService = Depends(get_crop_cycle_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[CropCycleResponse]:
    try:
        cycles = await service.list_cycles(str(user_id), str(farm_id), cycle_status)
    except FarmNotFoundError:
        raise _not_found() from None
    return [CropCycleResponse.model_validate(c) for c in cycles]


@router.get("/crop-cycles/{cycle_id}", response_model=CropCycleResponse)
async def get_cycle(
    cycle_id: uuid.UUID,
    service: CropCycleService = Depends(get_crop_cycle_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropCycleResponse:
    try:
        cycle = await service.get_cycle(str(user_id), str(cycle_id))
    except CropCycleNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    return CropCycleResponse.model_validate(cycle)


@router.patch("/crop-cycles/{cycle_id}", response_model=CropCycleResponse)
async def update_cycle(
    cycle_id: uuid.UUID,
    data: CropCycleUpdate,
    service: CropCycleService = Depends(get_crop_cycle_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CropCycleResponse:
    try:
        cycle = await service.update_cycle(
            str(user_id), str(cycle_id), **data.model_dump(exclude_unset=True)
        )
    except CropCycleNotFoundError:
        raise _not_found() from None
    except FarmNotFoundError:
        raise _not_found() from None
    except FarmPermissionError:
        raise _forbidden() from None
    except CropCycleStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": str(e), "error_code": "CROP_CYCLE_INVALID_TRANSITION"},
        ) from None
    return CropCycleResponse.model_validate(cycle)
