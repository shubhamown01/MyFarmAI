"""Admin view of the §10 cloud-AI quota (directive §4 dashboard, API level).

Read-only: per-user usage in the current window. Admin role enforced
server-side (same gate pattern as the selfie review queue).
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user_id
from app.api.v1.chat import get_settings
from app.api.v1.verification import _require_admin
from app.core.config import Settings
from app.db.session import db_manager
from app.services.ai_quota import ausage_rows, window_start_for

router = APIRouter(tags=["Admin"])


@router.get("/admin/ai-quota")
async def admin_ai_quota(
    limit: int = Query(default=50, ge=1, le=200),
    user_id: uuid.UUID = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Per-user §10 cloud-AI usage for the current window (admin only)."""
    window_hours = settings.cloud_ai_quota_window_hours
    async with db_manager.session() as session:
        await _require_admin(session, user_id)
        items = await ausage_rows(
            session,
            limit=settings.cloud_ai_quota_limit,
            window_hours=window_hours,
        )
    return {
        "window_start": window_start_for(datetime.now(UTC), window_hours).isoformat(),
        "window_hours": window_hours,
        "items": items[:limit],
        "count": len(items[:limit]),
    }
