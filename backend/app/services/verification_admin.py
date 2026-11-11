"""Administrator approval of pending registrations (MFAI-025, option c).

Self-registered accounts start as ``pending_verification`` and are denied
every plot and farmer-profile write by ``require_verified_user``. Wave 1/2
only offered a selfie-review path, and no client could submit a selfie, so
onboarding dead-ended for every self-signup.

This module is the non-biometric path: an authenticated administrator
approves or rejects a pending account explicitly. Every transition is
recorded as a :class:`VerificationEvent` carrying the reviewer identity,
the target account and the outcome. No default administrator is created
here — provisioning is an owner operation (see
``docs/security/ADMIN_ACCOUNT_PROCEDURE.md``).
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.identity import VerificationEvent
from app.db.models.user import User

# Only a freshly self-registered account can be decided. ``active`` and
# ``verified`` are already through the gate; ``rejected`` is terminal and
# must go through account recovery, not a second click.
DECIDABLE_STATUS = "pending_verification"


class PendingUserNotFoundError(Exception):
    """No user with the given id."""


class InvalidTransitionError(Exception):
    """The account is not in a state this decision may change."""


class SelfApprovalError(Exception):
    """An administrator may not decide their own account."""


class ReasonRequiredError(Exception):
    """A rejection was requested without a reason."""


async def list_pending(
    session: AsyncSession, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """Accounts awaiting a decision, oldest first.

    Email is included because it is the only identifier an administrator can
    use to confirm they are approving the right person. Nothing else is:
    no password hash, no session data, no IP addresses.
    """
    rows = (
        (
            await session.execute(
                select(User)
                .where(User.verification_status == DECIDABLE_STATUS)
                .order_by(User.created_at)
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "email_verified": u.email_verified,
            "verification_status": u.verification_status,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]


async def decide(
    session: AsyncSession,
    reviewer_user_id: uuid.UUID,
    target_user_id: uuid.UUID,
    approve: bool,
    reason: str | None = None,
) -> dict[str, Any]:
    """Approve or reject a pending account; write the audit event.

    Raises on every invalid request instead of silently no-op'ing, so a
    caller cannot mistake a rejected operation for a successful one.
    """
    if reviewer_user_id == target_user_id:
        raise SelfApprovalError

    user = await session.get(User, target_user_id)
    if user is None:
        raise PendingUserNotFoundError
    if user.verification_status != DECIDABLE_STATUS:
        raise InvalidTransitionError

    now = datetime.now(UTC)
    if approve:
        user.verification_status = "verified"
        event_type = "VERIFICATION_APPROVED"
        details: dict[str, Any] = {
            "method": "admin_approval",
            "reviewer_id": str(reviewer_user_id),
            "target_user_id": str(target_user_id),
        }
    else:
        if not reason or not reason.strip():
            raise ReasonRequiredError
        user.verification_status = "rejected"
        event_type = "VERIFICATION_REJECTED"
        details = {
            "method": "admin_approval",
            "reviewer_id": str(reviewer_user_id),
            "target_user_id": str(target_user_id),
            "reason": reason.strip()[:255],
        }

    session.add(VerificationEvent(user_id=user.id, event_type=event_type, details=details))
    await session.flush()
    return {
        "user_id": str(user.id),
        "verification_status": user.verification_status,
        "decided_at": now.isoformat(),
        "reviewer_id": str(reviewer_user_id),
    }
