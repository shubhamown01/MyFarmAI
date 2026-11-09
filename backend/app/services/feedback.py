"""Feedback service: create + list feedback rows (E1).

Very small — no photo/file handling; the owner can reply by email since
``email`` is plain text (not hashed), surfaced in list responses only
when the tester is anonymous (email absent).
"""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.feedback import Feedback as FeedbackModel

VALID_CATEGORIES = {"bug", "feature", "question", "praise"}


class FeedbackCreateError(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = "FEEDBACK_INVALID"


class FeedbackService:
    """Tiny synchronous-ish service that writes one Feedback row."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        category: str,
        message: str,
        email: str | None = None,
        app_version: str | None = None,
    ) -> uuid.UUID:
        if category not in VALID_CATEGORIES:
            raise FeedbackCreateError(422, f"invalid category: {category}")
        if len(message) < 5 or len(message) > 2000:
            raise FeedbackCreateError(422, "message must be 5–2000 chars")
        row = FeedbackModel(
            # anonymous submissions carry no user — a random uuid would violate
            # the user_id FK on Postgres (SQLite does not enforce it, which is
            # why tests passed without this).
            user_id=None,
            email=email or "",
            category=category,
            message=message,
            app_version=app_version,
        )
        self.session.add(row)
        await self.session.flush()
        return row.id  # type: ignore[no-any-return]

    async def list_all(
        self, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.session.scalar(
            select(func.count()).select_from(FeedbackModel)
        )
        rows = (
            await self.session.execute(
                select(FeedbackModel)
                .order_by(FeedbackModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars().all()
        items = []
        for r in rows:
            items.append({
                "id": str(r.id),
                "email": r.email,
                "category": r.category,
                "message": r.message,
                "app_version": r.app_version,
                "created_at": str(r.created_at) if r.created_at else None,
            })
        return items, total or 0
