"""Farmer profile + onboarding API endpoints (E5).

GET /me/onboarding uses only the authentication gate — pending users must
be able to see their own progress (directive §12: resume incomplete
onboarding). Profile mutation requires the verified-status gate (directive
§8: profile creation follows required verification steps).
"""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.auth import get_current_user_id, require_verified_user
from app.core.config import Settings
from app.db.session import db_manager
from app.schemas.profile import (
    FarmerProfileResponse,
    FarmerProfileUpdate,
    OnboardingStatusResponse,
)
from app.services.profile import ProfileNotFoundError, ProfileService

router = APIRouter(tags=["Profile"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_profile_service() -> AsyncIterator[ProfileService]:
    async with db_manager.session() as session:
        yield ProfileService(session)


@router.get("/me/onboarding", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    service: ProfileService = Depends(get_profile_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> OnboardingStatusResponse:
    try:
        state = await service.onboarding_status(str(user_id))
    except ProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "session invalid or expired", "error_code": "SESSION_INVALID"},
        ) from None
    return OnboardingStatusResponse(
        verification_status=str(state["verification_status"]),
        steps=state["steps"],  # type: ignore[arg-type]
        next_step=state["next_step"],  # type: ignore[arg-type]
        complete=bool(state["complete"]),
    )


@router.get("/me/farmer-profile", response_model=FarmerProfileResponse)
async def get_farmer_profile(
    service: ProfileService = Depends(get_profile_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> FarmerProfileResponse:
    profile = await service.get_profile(str(user_id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "profile not created yet", "error_code": "PROFILE_NOT_FOUND"},
        )
    return FarmerProfileResponse.model_validate(profile)


@router.put("/me/farmer-profile", response_model=FarmerProfileResponse)
async def save_farmer_profile(
    data: FarmerProfileUpdate,
    service: ProfileService = Depends(get_profile_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> FarmerProfileResponse:
    profile = await service.save_profile(str(user_id), **data.model_dump(exclude_unset=True))
    return FarmerProfileResponse.model_validate(profile)
