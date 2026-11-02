"""Admin manual review of selfie verifications (E3 wave 2).

Raw captures exist ONLY until a decision is made: approve/reject
immediately deletes the file from disk (``deleted_at`` stamped even when
the file is already gone — idempotent). The only access path to raw bytes
is :func:`stream_selfie`, which the admin router wraps in a FileResponse;
no path, filename, or URL ever appears in an API response.

``purge_expired`` is the retention safety net: rows left ``pending_review``
past ``settings.selfie_retention_days`` are auto-rejected (reason
``retention_expired``) and their files deleted. It is invoked at the start
of each admin queue listing (wave 2); a scheduled job is wave-3/ops work.
"""

import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.identity import SelfieVerification, VerificationEvent
from app.db.models.user import User

log = logging.getLogger(__name__)

RETENTION_REASON = "retention_expired"


class SelfieNotFoundError(Exception):
    """No verification row with the given id."""


class AlreadyReviewedError(Exception):
    """The row already has a terminal status."""


class ReasonRequiredError(Exception):
    """A rejection was requested without a reason."""


class SelfieDeletedError(Exception):
    """The raw file has been deleted (post-decision)."""


def _delete_file(row: SelfieVerification) -> None:
    """Unlink the raw capture and stamp deleted_at (idempotent)."""
    try:
        os.unlink(row.storage_path)
    except FileNotFoundError:
        log.warning("selfie raw file already missing: id=%s", row.id)
    except OSError:
        log.exception("selfie raw file deletion failed: id=%s", row.id)
        return  # never claim deleted when unlink failed; retention retries
    row.deleted_at = datetime.now(UTC)


def _row_public(row: SelfieVerification) -> dict[str, Any]:
    """Queue projection — NEVER includes storage_path or any file reference."""
    return {
        "id": str(row.id),
        "user_id": str(row.user_id),
        "created_at": row.created_at.isoformat(),
        "challenge_completed": row.challenge_completed,
        "vl_hint": row.vl_hint,
    }


async def list_queue(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """Pending-review rows, oldest first (no paths)."""
    rows = (
        (
            await session.execute(
                select(SelfieVerification)
                .where(SelfieVerification.status == "pending_review")
                .order_by(SelfieVerification.created_at)
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [_row_public(r) for r in rows]


async def decide(
    session: AsyncSession,
    reviewer_user_id: uuid.UUID,
    selfie_id: uuid.UUID,
    approve: bool,
    reason: str | None = None,
) -> dict[str, Any]:
    """Apply the reviewer's final decision and immediately delete the raw file."""
    row = await session.get(SelfieVerification, selfie_id)
    if row is None:
        raise SelfieNotFoundError
    if row.status != "pending_review":
        raise AlreadyReviewedError

    now = datetime.now(UTC)
    user = await session.get(User, row.user_id)
    assert user is not None  # FK guarantees existence

    if approve:
        row.status = "approved"
        user.verification_status = "verified"
        event_type = "VERIFICATION_APPROVED"
        details: dict[str, Any] = {"selfie_id": str(row.id)}
    else:
        if not reason or not reason.strip():
            raise ReasonRequiredError
        row.status = "rejected"
        row.rejection_reason = reason.strip()[:255]
        user.verification_status = "rejected"
        event_type = "VERIFICATION_REJECTED"
        details = {"selfie_id": str(row.id), "reason": row.rejection_reason}

    row.reviewed_by = reviewer_user_id
    row.reviewed_at = now
    details["reviewer_id"] = str(reviewer_user_id)
    session.add(VerificationEvent(user_id=user.id, event_type=event_type, details=details))
    _delete_file(row)
    return {
        "status": row.status,
        "user_verification_status": user.verification_status,
        "raw_file_deleted": row.deleted_at is not None,
    }


async def stream_selfie(
    session: AsyncSession, admin_user_id: uuid.UUID, selfie_id: uuid.UUID
) -> tuple[str, str]:
    """Return (path, mime_type) for admin-only raw-byte streaming.

    The ONLY access path to raw bytes. Audits REVIEW_VIEWED per fetch
    (no file paths in the audit payload).
    """
    row = await session.get(SelfieVerification, selfie_id)
    if row is None:
        raise SelfieNotFoundError
    if row.deleted_at is not None or not os.path.isfile(row.storage_path):
        raise SelfieDeletedError
    session.add(
        VerificationEvent(
            user_id=row.user_id,
            event_type="REVIEW_VIEWED",
            details={"selfie_id": str(row.id), "viewer_id": str(admin_user_id)},
        )
    )
    return row.storage_path, row.mime_type


async def purge_expired(session: AsyncSession, retention_days: int) -> int:
    """Auto-reject pending rows older than the retention window; return count."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    rows = (
        (
            await session.execute(
                select(SelfieVerification)
                .where(SelfieVerification.status == "pending_review")
                .where(SelfieVerification.created_at < cutoff)
            )
        )
        .scalars()
        .all()
    )
    for row in rows:
        row.status = "rejected"
        row.rejection_reason = RETENTION_REASON
        row.reviewed_at = datetime.now(UTC)
        user = await session.get(User, row.user_id)
        if user is not None:
            user.verification_status = "rejected"
        session.add(
            VerificationEvent(
                user_id=row.user_id,
                event_type="VERIFICATION_REJECTED",
                details={
                    "selfie_id": str(row.id),
                    "reason": RETENTION_REASON,
                    "auto": True,
                },
            )
        )
        _delete_file(row)
    if rows:
        # Flush before callers re-query in the same session (autoflush=False
        # would otherwise still see pending_review in list_queue).
        await session.flush()
        log.info("retention purge auto-rejected %d stale selfie(s)", len(rows))
    return len(rows)
