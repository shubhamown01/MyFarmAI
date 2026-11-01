"""Dashboard API endpoints (P7A-01)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.auth import get_current_user_id
from app.db.session import db_manager
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import DashboardService
from app.services.farm import FarmNotFoundError, FarmPermissionError, FarmService

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={
        404: {"description": "Farm not found or not a member (no existence leak)"},
    },
)
async def get_dashboard(
    farm_id: str = Query(..., description="Farm to assemble the dashboard for"),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DashboardResponse:
    async with db_manager.session() as session:
        service = DashboardService(session, FarmService(session))
        try:
            return await service.get_dashboard(str(user_id), farm_id)
        except (FarmNotFoundError, FarmPermissionError):
            # Non-members get 404, not 403 — farm existence is not revealed.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
            ) from None
