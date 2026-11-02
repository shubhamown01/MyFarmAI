"""Passwordless email-OTP registration tests (E1) — async mode (aiosqlite)."""

from collections import defaultdict

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.db.models.identity import ContactVerification
from app.db.models.user import User
from app.db.session import db_manager
from app.services.delivery import DevModeEmailDelivery

pytestmark = pytest.mark.usefixtures("async_initialized_db")

REQUEST_URL = "/api/v1/auth/register/email/request-otp"
VERIFY_URL = "/api/v1/auth/register/email/verify"
EMAIL = "farmer@example.com"


# -- helpers ----------------------------------------------------------------


def _capture_deliveries(monkeypatch: pytest.MonkeyPatch) -> defaultdict[str, list[str]]:
    """Class-level patch: the factory builds a fresh instance per request."""
    captured: defaultdict[str, list[str]] = defaultdict(list)

    async def fake_send_otp(self, destination: str, code: str) -> None:
        captured[destination].append(code)

    monkeypatch.setattr(DevModeEmailDelivery, "send_otp", fake_send_otp)
    return captured


async def _backdate_row(email: str, *, created_ago: int, expires_in: int) -> None:
    """Backdate created_at/expires_in for the pending row (direct DB write)."""
    from datetime import UTC, datetime, timedelta

    async with db_manager.session() as session:
        row = (
            await session.execute(
                select(ContactVerification)
                .where(ContactVerification.destination == email)
                .where(ContactVerification.consumed_at.is_(None))
                .order_by(ContactVerification.created_at.desc())
                .limit(1)
            )
        ).scalar_one()
        now = datetime.now(UTC)
        row.created_at = now - timedelta(seconds=created_ago)
        row.expires_at = now + timedelta(seconds=expires_in)
        await session.commit()


# -- tests --------------------------------------------------------------------


class TestEmailOtpRegistration:
    async def test_request_verify_and_me(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = _capture_deliveries(monkeypatch)

        resp = await async_client.post(REQUEST_URL, json={"email": EMAIL})
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == (
            "If the email address is valid, a verification code has been sent."
        )
        codes = captured[EMAIL]
        assert len(codes) == 1
        assert len(codes[0]) == 6 and codes[0].isdigit()

        resp = await async_client.post(VERIFY_URL, json={"email": EMAIL, "code": codes[0]})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user"]["email"] == EMAIL
        assert body["access_token"] is None  # web: cookie, not body token
        assert "myfarmai_session=" in resp.headers.get("set-cookie", "")

        me = await async_client.get("/api/v1/auth/me")
        assert me.status_code == 200, me.text
        assert me.json()["email"] == EMAIL

        async with db_manager.session() as session:
            user = (await session.execute(select(User).where(User.email == EMAIL))).scalar_one()
            # E3: self-signup activation lands in pending_verification.
            assert user.verification_status == "pending_verification"

    async def test_wrong_code_invalid_and_attempts_persist(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = _capture_deliveries(monkeypatch)
        await async_client.post(REQUEST_URL, json={"email": EMAIL})
        code = captured[EMAIL][0]
        wrong = "000000" if code != "000000" else "111111"

        resp = await async_client.post(VERIFY_URL, json={"email": EMAIL, "code": wrong})
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OTP_INVALID"

        # Second wrong attempt on the SAME pending row — attempts persisted.
        resp = await async_client.post(VERIFY_URL, json={"email": EMAIL, "code": wrong})
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OTP_INVALID"

        # Prove persistence in the DB, not just identical responses.
        async with db_manager.session() as session:
            row = (
                await session.execute(
                    select(ContactVerification).where(ContactVerification.destination == EMAIL)
                )
            ).scalar_one()
            assert row.attempts == 2, row.attempts

    async def test_expired_code(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = _capture_deliveries(monkeypatch)
        await async_client.post(REQUEST_URL, json={"email": EMAIL})
        await _backdate_row(EMAIL, created_ago=60, expires_in=-60)
        resp = await async_client.post(
            VERIFY_URL, json={"email": EMAIL, "code": captured[EMAIL][0]}
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OTP_EXPIRED"

    async def test_max_attempts(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _capture_deliveries(monkeypatch)
        await async_client.post(REQUEST_URL, json={"email": EMAIL})

        for i in range(5):
            resp = await async_client.post(
                VERIFY_URL, json={"email": EMAIL, "code": f"1000{i:02d}"}
            )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OTP_MAX_ATTEMPTS"

    async def test_resend_cooldown(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _capture_deliveries(monkeypatch)
        assert (await async_client.post(REQUEST_URL, json={"email": EMAIL})).status_code == 200
        resp = await async_client.post(REQUEST_URL, json={"email": EMAIL})
        assert resp.status_code == 429, resp.text
        assert resp.json()["error_code"] == "OTP_RESEND_COOLDOWN"
        assert resp.headers.get("retry-after") == "60"

    async def test_no_duplicate_user(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _capture_deliveries(monkeypatch)
        await async_client.post(REQUEST_URL, json={"email": EMAIL})
        await _backdate_row(EMAIL, created_ago=600, expires_in=600)  # clear the cooldown
        await async_client.post(REQUEST_URL, json={"email": EMAIL})

        async with db_manager.session() as session:
            count = (
                await session.execute(
                    select(func.count()).select_from(User).where(User.email == EMAIL)
                )
            ).scalar_one()
        assert count == 1

    async def test_pending_user_cannot_login(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _capture_deliveries(monkeypatch)
        await async_client.post(REQUEST_URL, json={"email": EMAIL})
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": "not-the-real-password-1!"},
        )
        assert resp.status_code == 401, resp.text
        assert resp.json()["error_code"] == "INVALID_CREDENTIALS"
