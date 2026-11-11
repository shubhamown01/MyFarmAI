"""Verification API endpoints (E3 wave 1 — selfie liveness ingest).

Selfie capture flow: consent → challenge → upload. Wave 1 stops at
``pending_review`` — the admin review queue is wave 2. Uploaded files are
re-encoded (all metadata/EXIF stripped) into a 0700 server-internal
directory; no storage path, filename, or URL is ever returned to a client.

Rate limiting (documented choice): the global middleware is path-scoped
only, so a simple per-user hourly cap is enforced here by counting
VerificationEvent rows (CHALLENGE_ISSUED) in the last hour — 10 per user,
applied to the challenge endpoint (upload is inherently challenge-gated,
single-use).
"""

import io
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user_id, get_settings
from app.core.client_ip import client_ip_from
from app.core.config import Settings
from app.db.models.identity import ConsentRecord, SelfieVerification, VerificationEvent
from app.db.models.user import User
from app.db.session import db_manager
from app.services import selfie as selfie_service
from app.services import selfie_review, verification_admin
from app.services.selfie import ChallengeInvalidError

router = APIRouter(prefix="/verification", tags=["Verification"])

_MIN_DIM = 512
_MAX_DIM = 4096
_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_CHALLENGES_PER_HOUR = 10
_MAGIC = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)
_EXT = {"jpeg": ".jpg", "png": ".png"}


def _client_ip(request: Request) -> str | None:
    return client_ip_from(request, request.app.state.settings.trusted_proxy_cidrs_list)


def _sniff_format(head: bytes) -> str | None:
    for magic, fmt in _MAGIC:
        if head.startswith(magic):
            return fmt
    return None


def _err(status_code: int, detail: str, error_code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code, detail={"detail": detail, "error_code": error_code}
    )


async def _pending_user_with_consent(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Shared preconditions for challenge/upload: pending_verification + consent."""
    user = await session.get(User, user_id)
    if user is None:
        raise _err(status.HTTP_401_UNAUTHORIZED, "authentication required", "NOT_AUTHENTICATED")
    if user.verification_status != "pending_verification":
        raise _err(409, "selfie verification is not pending", "NOT_PENDING")
    consent = (
        await session.execute(
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .where(ConsentRecord.consent_type == "selfie_liveness")
            .order_by(ConsentRecord.granted_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if consent is None:
        raise _err(409, "consent required before selfie verification", "CONSENT_REQUIRED")


@router.post("/selfie/consent")
async def grant_consent(
    request: Request,
    settings: Settings = Depends(get_settings),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Record selfie-liveness processing consent (E3)."""
    ip = _client_ip(request)
    async with db_manager.session() as session:
        session.add(
            ConsentRecord(
                user_id=user_id,
                consent_type="selfie_liveness",
                policy_version=settings.selfie_policy_version,
                ip_address=ip,
            )
        )
        session.add(
            VerificationEvent(
                user_id=user_id,
                event_type="CONSENT_GRANTED",
                details={"policy_version": settings.selfie_policy_version},
                ip_address=ip,
            )
        )
    return {"status": "granted"}


@router.post("/selfie/challenge")
async def issue_challenge(
    request: Request,
    settings: Settings = Depends(get_settings),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Issue a 2-action liveness challenge (single-use, 300s, session-bound)."""
    ip = _client_ip(request)
    async with db_manager.session() as session:
        await _pending_user_with_consent(session, user_id)
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        issued = (
            await session.execute(
                select(func.count())
                .select_from(VerificationEvent)
                .where(VerificationEvent.user_id == user_id)
                .where(VerificationEvent.event_type == "CHALLENGE_ISSUED")
                .where(VerificationEvent.created_at > hour_ago)
            )
        ).scalar_one()
        if issued >= _CHALLENGES_PER_HOUR:
            raise _err(429, "too many challenges requested; try again later", "RATE_LIMITED")

        challenge_id, actions = selfie_service.issue_challenge(user_id)
        session.add(
            VerificationEvent(
                user_id=user_id,
                event_type="CHALLENGE_ISSUED",
                details={"challenge_id": challenge_id},
                ip_address=ip,
            )
        )
    return {
        "challenge_id": challenge_id,
        "actions": list(actions),
        "expires_in": selfie_service.CHALLENGE_TTL_SECONDS,
    }


@router.post("/selfie/upload")
async def upload_selfie(
    request: Request,
    file: UploadFile,
    challenge_id: str = Form(...),
    settings: Settings = Depends(get_settings),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Ingest a liveness selfie for manual review (E3 wave 1).

    Validation order: pending status → consent → challenge consume (atomic,
    single-use) → magic bytes → size → dimensions → metadata-stripping
    re-encode → 0700/0600 storage. The response never contains a storage
    path, filename, or URL.
    """
    ip = _client_ip(request)

    async with db_manager.session() as session:
        await _pending_user_with_consent(session, user_id)
        try:
            actions = selfie_service.consume_challenge(challenge_id, user_id)
        except ChallengeInvalidError:
            raise _err(
                422, "challenge invalid, expired, or already used", "CHALLENGE_INVALID"
            ) from None

        data = await file.read(_MAX_IMAGE_BYTES + 1)
        fmt = _sniff_format(data[:12])
        if fmt is None:
            raise _err(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "unsupported image format (jpeg/png only)",
                "UNSUPPORTED_MEDIA_TYPE",
            )
        if len(data) > _MAX_IMAGE_BYTES:
            raise _err(413, "image too large (max 5 MiB)", "IMAGE_TOO_LARGE")

        try:
            img = Image.open(io.BytesIO(data))
            width, height = img.size
            if not (_MIN_DIM <= width <= _MAX_DIM and _MIN_DIM <= height <= _MAX_DIM):
                raise _err(
                    422,
                    f"image dimensions must be {_MIN_DIM}-{_MAX_DIM}px",
                    "IMAGE_DIMENSIONS",
                )
            img.load()  # decode only after the dimension gate (memory-DoS guard)
        except HTTPException:
            raise
        except Exception:
            raise _err(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "unreadable image", "UNSUPPORTED_MEDIA_TYPE"
            ) from None

        # Re-encode to strip ALL metadata (EXIF/GPS/ICC) — nothing from the
        # camera is copied into the stored file.
        clean = io.BytesIO()
        if fmt == "jpeg":
            img.convert("RGB").save(clean, "JPEG", quality=85)
        else:
            img.save(clean, "PNG")
        stored = clean.getvalue()

        storage_dir = Path(settings.selfie_storage_dir)
        storage_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(storage_dir, 0o700)
        filename = f"{uuid.uuid4().hex}{_EXT[fmt]}"
        path = storage_dir / filename
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(stored)
        os.chmod(path, 0o600)

        session.add(
            SelfieVerification(
                user_id=user_id,
                challenge_id=challenge_id,
                storage_path=str(path),
                mime_type=f"image/{fmt}",
                file_size=len(stored),
                challenge_completed=True,
                status="pending_review",
                vl_hint=" ".join(actions)[:20] or None,
            )
        )
        session.add(
            VerificationEvent(
                user_id=user_id,
                event_type="CAPTURE_UPLOADED",
                details={"mime_type": f"image/{fmt}", "file_size": len(stored)},
                ip_address=ip,
            )
        )
    return {"status": "received", "review_state": "pending_review"}


# -- admin manual review (E3 wave 2) ------------------------------------------


class DecisionRequest(BaseModel):
    approved: bool
    reason: str | None = Field(default=None, max_length=255)


async def _require_admin(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Server-side admin role gate (mirrors auth.py admin route pattern)."""
    user = await session.get(User, user_id)
    if user is None or user.role.value != "admin":
        raise _err(403, "admin role required", "ADMIN_REQUIRED")


def _map_review_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, selfie_review.SelfieNotFoundError):
        return _err(404, "selfie not found", "SELFIE_NOT_FOUND")
    if isinstance(exc, selfie_review.AlreadyReviewedError):
        return _err(409, "selfie already reviewed", "ALREADY_REVIEWED")
    if isinstance(exc, selfie_review.ReasonRequiredError):
        return _err(422, "a reason is required to reject", "REASON_REQUIRED")
    if isinstance(exc, selfie_review.SelfieDeletedError):
        return _err(404, "selfie raw file has been deleted", "SELFIE_DELETED")
    raise exc  # pragma: no cover


@router.get("/admin/selfies")
async def admin_queue(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Admin manual-review queue (pending rows only; no storage paths).

    Retention safety net: rows pending longer than ``selfie_retention_days``
    are auto-rejected and their raw files deleted before listing.
    """
    async with db_manager.session() as session:
        await _require_admin(session, user_id)
        await selfie_review.purge_expired(session, settings.selfie_retention_days)
        items = await selfie_review.list_queue(session, limit=limit, offset=offset)
    return {"items": items, "count": len(items)}


@router.post("/admin/selfies/{selfie_id}/decision")
async def admin_decide(
    selfie_id: uuid.UUID,
    body: DecisionRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Final decision: flips status + user verification state, deletes the raw
    file immediately (raw captures are kept only until the decision)."""
    try:
        async with db_manager.session() as session:
            await _require_admin(session, user_id)
            result = await selfie_review.decide(
                session, user_id, selfie_id, body.approved, body.reason
            )
    except Exception as exc:
        raise _map_review_errors(exc) from None
    return result


@router.get("/admin/selfies/{selfie_id}/raw")
async def admin_raw(
    selfie_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FileResponse:
    """Admin-only streaming access to the raw capture (the only such path)."""
    try:
        async with db_manager.session() as session:
            await _require_admin(session, user_id)
            path, mime_type = await selfie_review.stream_selfie(session, user_id, selfie_id)
    except Exception as exc:
        raise _map_review_errors(exc) from None
    return FileResponse(path, media_type=mime_type)


# -- administrator approval of pending registrations (MFAI-025) --------------
#
# The non-biometric verification path. Self-signups land in
# ``pending_verification`` and are denied every plot/profile write; an
# administrator decides here, and the decision is audited. Self-approval is
# rejected server-side, not hidden in the UI.


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    reason: str | None = Field(default=None, max_length=255)


def _map_approval_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, verification_admin.PendingUserNotFoundError):
        return _err(404, "user not found", "USER_NOT_FOUND")
    if isinstance(exc, verification_admin.InvalidTransitionError):
        return _err(409, "account is not awaiting approval", "INVALID_TRANSITION")
    if isinstance(exc, verification_admin.SelfApprovalError):
        return _err(403, "administrators cannot decide their own account", "SELF_APPROVAL")
    if isinstance(exc, verification_admin.ReasonRequiredError):
        return _err(422, "a reason is required to reject", "REASON_REQUIRED")
    raise exc  # pragma: no cover


@router.get("/admin/pending-users")
async def admin_pending_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Accounts awaiting an approval decision (administrators only)."""
    async with db_manager.session() as session:
        await _require_admin(session, user_id)
        items = await verification_admin.list_pending(session, limit=limit, offset=offset)
    return {"items": items, "count": len(items)}


@router.post("/admin/users/{target_user_id}/decision")
async def admin_user_decision(
    target_user_id: uuid.UUID,
    body: ApprovalDecisionRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Approve or reject a pending account; the outcome is audited."""
    try:
        async with db_manager.session() as session:
            await _require_admin(session, user_id)
            return await verification_admin.decide(
                session, user_id, target_user_id, body.approved, body.reason
            )
    except Exception as exc:
        raise _map_approval_errors(exc) from None
