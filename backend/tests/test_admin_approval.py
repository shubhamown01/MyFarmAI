"""Administrator approval of pending registrations (MFAI-025, option c).

Covers the acceptance cases: pending-on-signup, the write gate, role
authorization, self-approval, invalid transitions, audit records, and the
post-approval workflow.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.identity import VerificationEvent
from app.db.models.user import User, UserRole
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")

PENDING_URL = "/api/v1/verification/admin/pending-users"
DECISION_URL = "/api/v1/verification/admin/users/{user_id}/decision"
LOGIN_URL = "/api/v1/auth/login"
ONBOARDING_URL = "/api/v1/me/onboarding"

ADMIN_EMAIL = "approval-admin@example.com"
ADMIN_PASSWORD = "Admin-pass-1!"


async def _make_admin() -> None:
    async with db_manager.session() as session:
        session.add(
            User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            )
        )


async def _make_pending(email: str) -> uuid.UUID:
    """A fresh self-signup: pending, email already proven by OTP."""
    async with db_manager.session() as session:
        user = User(
            email=email,
            password_hash=hash_password("User-pass-1!"),
            verification_status="pending_verification",
            email_verified=True,
        )
        session.add(user)
        await session.flush()
        return user.id


async def _login(client: AsyncClient, email: str, password: str) -> None:
    resp = await client.post(LOGIN_URL, json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text


async def _events(user_id: uuid.UUID) -> list[VerificationEvent]:
    async with db_manager.session() as session:
        return list(
            (
                await session.execute(
                    select(VerificationEvent).where(VerificationEvent.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )


class TestPendingState:
    async def test_new_signup_is_pending(self, async_client: AsyncClient) -> None:
        """Case 1: a self-registered account starts pending, not active."""
        target = await _make_pending("signup-pending@example.com")
        async with db_manager.session() as session:
            user = await session.get(User, target)
            assert user is not None
            assert user.verification_status == "pending_verification"

    async def test_pending_user_cannot_write_protected_data(
        self, async_client: AsyncClient
    ) -> None:
        """Case 2: the verified gate still denies plots and profile writes."""
        await _make_pending("pending-writer@example.com")
        await _login(async_client, "pending-writer@example.com", "User-pass-1!")

        resp = await async_client.put(
            "/api/v1/me/home-location", json={"latitude": 18.5, "longitude": 73.8}
        )
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "USER_NOT_VERIFIED"

        resp = await async_client.put("/api/v1/me/farmer-profile", json={"full_name": "X"})
        assert resp.status_code == 403, resp.text

    async def test_pending_user_sees_own_status(self, async_client: AsyncClient) -> None:
        """The user can read their own onboarding state while pending."""
        await _make_pending("pending-reader@example.com")
        await _login(async_client, "pending-reader@example.com", "User-pass-1!")
        resp = await async_client.get(ONBOARDING_URL)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["verification_status"] == "pending_verification"
        assert body["complete"] is False
        assert body["next_step"] == "verification"


class TestAuthorization:
    async def test_normal_user_cannot_approve_another(
        self, async_client: AsyncClient
    ) -> None:
        """Case 3: a non-admin cannot approve someone else."""
        target = await _make_pending("victim@example.com")
        await _make_pending("civilian@example.com")
        await _login(async_client, "civilian@example.com", "User-pass-1!")

        resp = await async_client.post(
            DECISION_URL.format(user_id=target), json={"approved": True}
        )
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"

    async def test_normal_user_cannot_approve_self(self, async_client: AsyncClient) -> None:
        """Case 4: self-approval fails on the role gate, not the UI."""
        me = await _make_pending("self-approver@example.com")
        await _login(async_client, "self-approver@example.com", "User-pass-1!")
        resp = await async_client.post(
            DECISION_URL.format(user_id=me), json={"approved": True}
        )
        assert resp.status_code == 403, resp.text
        async with db_manager.session() as session:
            user = await session.get(User, me)
            assert user is not None
            assert user.verification_status == "pending_verification"

    async def test_unauthenticated_requests_rejected(self, async_client: AsyncClient) -> None:
        """Case 5: no session means no queue and no decision."""
        target = await _make_pending("anon-target@example.com")
        resp = await async_client.get(PENDING_URL)
        assert resp.status_code == 401, resp.text
        resp = await async_client.post(
            DECISION_URL.format(user_id=target), json={"approved": True}
        )
        assert resp.status_code == 401, resp.text

    async def test_admin_cannot_decide_own_account(self, async_client: AsyncClient) -> None:
        """An administrator with a pending row still cannot self-approve."""
        await _make_admin()
        async with db_manager.session() as session:
            admin = (
                await session.execute(select(User).where(User.email == ADMIN_EMAIL))
            ).scalar_one()
            admin.verification_status = "pending_verification"
            admin_id = admin.id
        await _login(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)

        resp = await async_client.post(
            DECISION_URL.format(user_id=admin_id), json={"approved": True}
        )
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "SELF_APPROVAL"


class TestDecision:
    async def test_admin_approves_and_it_is_audited(self, async_client: AsyncClient) -> None:
        """Cases 6 and 7: approval succeeds and leaves an audit record."""
        await _make_admin()
        target = await _make_pending("approve-me@example.com")
        await _login(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)

        queue = await async_client.get(PENDING_URL)
        assert queue.status_code == 200, queue.text
        assert [i["id"] for i in queue.json()["items"]] == [str(target)]
        # Queue projection carries no secrets.
        assert "password" not in queue.text and "hash" not in queue.text

        resp = await async_client.post(
            DECISION_URL.format(user_id=target), json={"approved": True}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["verification_status"] == "verified"

        events = await _events(target)
        assert len(events) == 1
        assert events[0].event_type == "VERIFICATION_APPROVED"
        assert events[0].details is not None
        assert events[0].details["method"] == "admin_approval"
        assert events[0].details["target_user_id"] == str(target)
        assert events[0].details["reviewer_id"] != str(target)

    async def test_approved_user_can_write(self, async_client: AsyncClient) -> None:
        """Case 8: the same account passes the gate after approval."""
        await _make_admin()
        target = await _make_pending("now-allowed@example.com")
        await _login(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = await async_client.post(
            DECISION_URL.format(user_id=target), json={"approved": True}
        )
        assert resp.status_code == 200, resp.text

        # Same client, new session for the approved user.
        await _login(async_client, "now-allowed@example.com", "User-pass-1!")
        resp = await async_client.put(
            "/api/v1/me/farmer-profile", json={"full_name": "Approved Farmer"}
        )
        assert resp.status_code == 200, resp.text

    async def test_rejection_requires_reason_and_is_terminal(
        self, async_client: AsyncClient
    ) -> None:
        """Case 9: invalid transitions and missing reasons fail safely."""
        await _make_admin()
        target = await _make_pending("reject-me@example.com")
        await _login(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)
        url = DECISION_URL.format(user_id=target)

        resp = await async_client.post(url, json={"approved": False})
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "REASON_REQUIRED"

        resp = await async_client.post(
            url, json={"approved": False, "reason": "identity could not be confirmed"}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["verification_status"] == "rejected"

        # A second decision on a terminal account is refused, not repeated.
        resp = await async_client.post(url, json={"approved": True})
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "INVALID_TRANSITION"

        events = await _events(target)
        assert [e.event_type for e in events] == ["VERIFICATION_REJECTED"]
        assert events[0].details is not None
        assert events[0].details["reason"] == "identity could not be confirmed"

    async def test_unknown_user_is_404(self, async_client: AsyncClient) -> None:
        await _make_admin()
        await _login(async_client, ADMIN_EMAIL, ADMIN_PASSWORD)
        resp = await async_client.post(
            DECISION_URL.format(user_id=uuid.uuid4()), json={"approved": True}
        )
        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "USER_NOT_FOUND"
