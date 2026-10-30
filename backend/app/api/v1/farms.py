"""Farm API endpoints (P5A-01)."""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.db.session import db_manager
from app.schemas.farm import (
    FarmCreate,
    FarmMemberAdd,
    FarmMemberResponse,
    FarmMemberRoleUpdate,
    FarmResponse,
    FarmUpdate,
)
from app.services.farm import (
    FarmNotFoundError,
    FarmPermissionError,
    FarmService,
    FarmUserNotFoundError,
)

router = APIRouter(tags=["Farms"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_farm_service(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[FarmService]:
    """FarmService bound to an async session that commits on clean completion."""
    async with db_manager.session() as session:
        yield FarmService(session)


@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    data: FarmCreate,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FarmResponse:
    farm = await service.create_farm(
        owner_id=str(user_id),
        name=data.name,
        description=data.description,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        timezone=data.timezone,
    )
    return FarmResponse.model_validate(farm)


@router.get("/farms", response_model=list[FarmResponse])
async def list_farms(
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[FarmResponse]:
    farms = await service.list_farms(str(user_id))
    return [FarmResponse.model_validate(f) for f in farms]


@router.get("/farms/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FarmResponse:
    try:
        farm = await service.get_farm(str(user_id), str(farm_id))
    except FarmNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
        ) from None
    return FarmResponse.model_validate(farm)


@router.patch("/farms/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: uuid.UUID,
    data: FarmUpdate,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FarmResponse:
    try:
        farm = await service.update_farm(
            str(user_id), str(farm_id), **data.model_dump(exclude_unset=True)
        )
    except FarmNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
        ) from None
    except FarmPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
        ) from None
    return FarmResponse.model_validate(farm)


@router.get("/farms/{farm_id}/members", response_model=list[FarmMemberResponse])
async def list_members(
    farm_id: uuid.UUID,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[FarmMemberResponse]:
    try:
        members = await service.list_members(str(user_id), str(farm_id))
    except FarmNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
        ) from None
    return [FarmMemberResponse.model_validate(m) for m in members]


@router.post(
    "/farms/{farm_id}/members",
    response_model=FarmMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    farm_id: uuid.UUID,
    data: FarmMemberAdd,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FarmMemberResponse:
    try:
        member = await service.add_member(str(user_id), str(farm_id), str(data.user_id), data.role)
    except FarmNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
        ) from None
    except FarmUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "user not found", "error_code": "USER_NOT_FOUND"},
        ) from None
    except FarmPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
        ) from None
    return FarmMemberResponse.model_validate(member)


def _member_error(e: Exception) -> HTTPException:
    if isinstance(e, FarmPermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
        )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"detail": "member not found", "error_code": "MEMBER_NOT_FOUND"},
    )


@router.delete("/farms/{farm_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    farm_id: uuid.UUID,
    member_user_id: uuid.UUID,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    try:
        await service.remove_member(str(user_id), str(farm_id), str(member_user_id))
    except (FarmNotFoundError, FarmPermissionError) as e:
        raise _member_error(e) from None


@router.patch("/farms/{farm_id}/members/{member_user_id}", response_model=FarmMemberResponse)
async def update_member_role(
    farm_id: uuid.UUID,
    member_user_id: uuid.UUID,
    data: FarmMemberRoleUpdate,
    service: FarmService = Depends(get_farm_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FarmMemberResponse:
    try:
        member = await service.update_member_role(
            str(user_id), str(farm_id), str(member_user_id), data.role
        )
    except (FarmNotFoundError, FarmPermissionError) as e:
        raise _member_error(e) from None
    return FarmMemberResponse.model_validate(member)
