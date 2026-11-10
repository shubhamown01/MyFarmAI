"""Public feedback endpoint (E1): submit a bug report or feature request.

No auth required for submission (matches the APK download pattern). The
tester's email is collected only as an optional owner-reply field — no
passwords, OTPs, private farm data, or unnecessary PII are stored beyond
the masked category + message + optional app version.
"""

import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.auth import get_current_user_id
from app.db.models.user import User
from app.db.session import db_manager
from app.schemas.feedback import FeedbackRequest
from app.services.feedback import FeedbackCreateError, FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _err(status_code: int, detail: str, error_code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"detail": detail, "error_code": error_code},
    )


async def get_feedback_service() -> AsyncIterator[FeedbackService]:
    """FeedbackService bound to an async session that commits on clean request completion."""
    async with db_manager.session() as session:
        yield FeedbackService(session)


@router.post("/submit", include_in_schema=False)
async def submit_feedback(
    body: FeedbackRequest,
    service: FeedbackService = Depends(get_feedback_service),
) -> dict[str, Any]:
    """Submit brief, synthetic-safe feedback (optional email for reply).

    Anonymous when ``email`` omitted; category is validated server-side;
    no auth needed — mirrors the public APK-download guardrail.
    """
    try:
        row_id = await service.create(
            category=body.category,
            message=body.message,
            email=body.email,
            app_version=body.app_version,
        )
    except FeedbackCreateError as exc:
        raise _err(exc.status_code, exc.detail, exc.error_code) from None
    except Exception:  # pragma: no cover
        raise _err(500, "feedback storage failed", "INTERNAL") from None
    return {"status": "accepted", "id": str(row_id)}


@router.get("", status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_feedback(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: FeedbackService = Depends(get_feedback_service),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Admin/owner view of all feedback submissions (read-only aggregation)."""
    user = await service.session.get(User, user_id)
    if user is None or user.role.value != "admin":
        raise _err(403, "admin role required", "ADMIN_REQUIRED")
    items, total = await service.list_all(limit=limit, offset=offset)
    return {"items": items, "count": total}
