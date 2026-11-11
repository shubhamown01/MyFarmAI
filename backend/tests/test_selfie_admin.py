"""Admin selfie manual-review tests (E3 wave 2) — async mode (aiosqlite)."""

import io
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.identity import SelfieVerification, VerificationEvent
from app.db.models.user import User, UserRole
from app.db.session import db_manager
from app.services import selfie as selfie_service
from app.services.delivery import DevModeEmailDelivery

pytestmark = pytest.mark.usefixtures("async_initialized_db")

REQUEST_URL = "/api/v1/auth/register/email/request-otp"
VERIFY_URL = "/api/v1/auth/register/email/verify"
CONSENT_URL = "/api/v1/verification/selfie/consent"
CHALLENGE_URL = "/api/v1/verification/selfie/challenge"
UPLOAD_URL = "/api/v1/verification/selfie/upload"
QUEUE_URL = "/api/v1/verification/admin/selfies"
LOGIN_URL = "/api/v1/auth/login"


# -- helpers ------------------------------------------------------------------


def _capture_deliveries(monkeypatch: pytest.MonkeyPatch) -> defaultdict[str, list[str]]:
    captured: defaultdict[str, list[str]] = defaultdict(list)

    async def fake_send_otp(self, destination: str, code: str) -> None:
        captured[destination].append(code)

    monkeypatch.setattr(DevModeEmailDelivery, "send_otp", fake_send_otp)
    return captured


async def _signup_and_upload(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, email: str
) -> uuid.UUID:
    """Full wave-1 flow; leaves the client logged in as the applicant."""
    captured = _capture_deliveries(monkeypatch)
    await client.post(REQUEST_URL, json={"email": email})
    resp = await client.post(VERIFY_URL, json={"email": email, "code": captured[email][0], "password": "selfie-pass-123"})
    assert resp.status_code == 200, resp.text
    await client.post(CONSENT_URL)
    challenge = (await client.post(CHALLENGE_URL)).json()
    buf = io.BytesIO()
    Image.new("RGB", (640, 640), (90, 140, 90)).save(buf, "JPEG")
    resp = await client.post(
        UPLOAD_URL,
        files={"file": ("selfie.jpg", buf.getvalue(), "image/jpeg")},
        data={"challenge_id": challenge["challenge_id"]},
    )
    assert resp.status_code == 200, resp.text
    return await _user_id(email)


async def _user_id(email: str) -> uuid.UUID:
    async with db_manager.session() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        return user.id


async def _selfie_row(user_id: uuid.UUID) -> SelfieVerification:
    async with db_manager.session() as session:
        row = (
            await session.execute(
                select(SelfieVerification).where(SelfieVerification.user_id == user_id)
            )
        ).scalar_one()
        session.expunge(row)
        return row


async def _make_admin(client: AsyncClient, email: str) -> None:
    async with db_manager.session() as session:
        session.add(
            User(
                email=email,
                password_hash=hash_password("Admin-pass-1!"),
                role=UserRole.ADMIN,
            )
        )
    resp = await client.post(LOGIN_URL, json={"email": email, "password": "Admin-pass-1!"})
    assert resp.status_code == 200, resp.text


async def _login_user(client: AsyncClient, email: str) -> None:
    resp = await client.post(LOGIN_URL, json={"email": email, "password": "User-pass-1!"})
    assert resp.status_code == 200, resp.text


async def _make_plain_user(email: str) -> None:
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("User-pass-1!")))


@pytest.fixture
def clean_challenges():
    selfie_service._challenges.clear()
    selfie_service._user_latest.clear()
    yield
    selfie_service._challenges.clear()
    selfie_service._user_latest.clear()


@pytest.fixture
def selfie_dir(async_test_settings, tmp_path, monkeypatch):
    d = tmp_path / "selfies"
    monkeypatch.setattr(async_test_settings, "selfie_storage_dir", str(d))
    return d


# -- tests --------------------------------------------------------------------


class TestAdminAuthorization:
    async def test_non_admin_and_anonymous_blocked(self, async_client: AsyncClient) -> None:
        decision_url = f"{QUEUE_URL}/{uuid.uuid4()}/decision"
        raw_url = f"{QUEUE_URL}/{uuid.uuid4()}/raw"
        # Anonymous → 401 (get_current_user_id gate).
        assert (await async_client.get(QUEUE_URL)).status_code == 401
        assert (await async_client.post(decision_url, json={"approved": True})).status_code == 401
        assert (await async_client.get(raw_url)).status_code == 401

        # Authenticated non-admin → 403 ADMIN_REQUIRED on all three.
        await _make_plain_user("wave2-civilian@example.com")
        await _login_user(async_client, "wave2-civilian@example.com")
        resp = await async_client.get(QUEUE_URL)
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"
        resp = await async_client.post(decision_url, json={"approved": True})
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"
        resp = await async_client.get(raw_url)
        assert resp.status_code == 403, resp.text
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"


class TestAdminQueue:
    async def test_queue_lists_pending_without_paths(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "wave2-queue@example.com"
        await _signup_and_upload(async_client, monkeypatch, email)
        await _make_admin(async_client, "wave2-admin@example.com")

        resp = await async_client.get(QUEUE_URL)
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert set(item) == {"id", "user_id", "created_at", "challenge_completed", "vl_hint"}
        assert item["challenge_completed"] is True
        assert item["vl_hint"]  # hint shown, path never
        # No storage path / filename / URL anywhere in the payload.
        assert "path" not in resp.text and str(selfie_dir) not in resp.text


class TestAdminDecision:
    async def test_approve_verifies_user_and_deletes_file(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "wave2-approve@example.com"
        user_id = await _signup_and_upload(async_client, monkeypatch, email)
        row = await _selfie_row(user_id)
        assert Path(row.storage_path).is_file()
        await _make_admin(async_client, "wave2-admin2@example.com")

        resp = await async_client.post(f"{QUEUE_URL}/{row.id}/decision", json={"approved": True})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body == {
            "status": "approved",
            "user_verification_status": "verified",
            "raw_file_deleted": True,
        }
        # Raw file gone from disk; row terminal with reviewer + deleted_at.
        assert not Path(row.storage_path).exists()
        async with db_manager.session() as session:
            fresh = await session.get(SelfieVerification, row.id)
            assert fresh.status == "approved"
            assert fresh.reviewed_by is not None
            assert fresh.deleted_at is not None
            user = await session.get(User, user_id)
            assert user.verification_status == "verified"
            events = (
                (
                    await session.execute(
                        select(VerificationEvent).where(
                            VerificationEvent.user_id == user_id,
                            VerificationEvent.event_type == "VERIFICATION_APPROVED",
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1

        # Decision is final → 409.
        resp = await async_client.post(
            f"{QUEUE_URL}/{row.id}/decision", json={"approved": False, "reason": "late"}
        )
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "ALREADY_REVIEWED"

    async def test_reject_requires_reason(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "wave2-noreason@example.com"
        user_id = await _signup_and_upload(async_client, monkeypatch, email)
        row = await _selfie_row(user_id)
        await _make_admin(async_client, "wave2-admin3@example.com")

        resp = await async_client.post(f"{QUEUE_URL}/{row.id}/decision", json={"approved": False})
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "REASON_REQUIRED"
        # Nothing changed: still pending, file still on disk.
        assert Path(row.storage_path).is_file()
        async with db_manager.session() as session:
            fresh = await session.get(SelfieVerification, row.id)
            assert fresh.status == "pending_review"
            assert fresh.deleted_at is None

    async def test_reject_rejects_user_and_deletes_file(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "wave2-reject@example.com"
        user_id = await _signup_and_upload(async_client, monkeypatch, email)
        row = await _selfie_row(user_id)
        await _make_admin(async_client, "wave2-admin4@example.com")

        resp = await async_client.post(
            f"{QUEUE_URL}/{row.id}/decision",
            json={"approved": False, "reason": "picture of a picture"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "rejected"
        assert body["user_verification_status"] == "rejected"
        assert body["raw_file_deleted"] is True
        assert not Path(row.storage_path).exists()

        async with db_manager.session() as session:
            fresh = await session.get(SelfieVerification, row.id)
            assert fresh.rejection_reason == "picture of a picture"
            user = await session.get(User, user_id)
            assert user.verification_status == "rejected"
            event = (
                await session.execute(
                    select(VerificationEvent).where(
                        VerificationEvent.user_id == user_id,
                        VerificationEvent.event_type == "VERIFICATION_REJECTED",
                    )
                )
            ).scalar_one()
            assert event.details["reason"] == "picture of a picture"


class TestAdminRawStreaming:
    async def test_raw_streams_then_404_after_decision(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "wave2-raw@example.com"
        user_id = await _signup_and_upload(async_client, monkeypatch, email)
        row = await _selfie_row(user_id)
        stored = Path(row.storage_path).read_bytes()
        await _make_admin(async_client, "wave2-admin5@example.com")

        resp = await async_client.get(f"{QUEUE_URL}/{row.id}/raw")
        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content == stored
        # Per-view audit event, no path in the payload.
        async with db_manager.session() as session:
            event = (
                await session.execute(
                    select(VerificationEvent).where(
                        VerificationEvent.user_id == user_id,
                        VerificationEvent.event_type == "REVIEW_VIEWED",
                    )
                )
            ).scalar_one()
            assert str(row.id) in str(event.details)
        assert str(row.storage_path) not in str(event.details)

        # After the decision the raw bytes are gone forever.
        resp = await async_client.post(f"{QUEUE_URL}/{row.id}/decision", json={"approved": True})
        assert resp.status_code == 200, resp.text
        resp = await async_client.get(f"{QUEUE_URL}/{row.id}/raw")
        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "SELFIE_DELETED"


class TestRetentionPurge:
    async def test_aged_pending_rows_auto_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email_fresh = "wave2-fresh@example.com"
        await _signup_and_upload(async_client, monkeypatch, email_fresh)

        # Hand-craft an aged pending row with a real file on disk.
        old_email = "wave2-aged@example.com"
        async with db_manager.session() as session:
            session.add(User(email=old_email, password_hash=hash_password("User-pass-1!")))
        old_user_id = await _user_id(old_email)
        aged_path = selfie_dir / "aged-capture.jpg"
        aged_path.write_bytes(b"\xff\xd8\xffaged")
        cutoff = datetime.now(UTC) - timedelta(days=31)
        async with db_manager.session() as session:
            session.add(
                SelfieVerification(
                    user_id=old_user_id,
                    challenge_id="aged-challenge",
                    storage_path=str(aged_path),
                    mime_type="image/jpeg",
                    file_size=aged_path.stat().st_size,
                    challenge_completed=True,
                    status="pending_review",
                    created_at=cutoff,
                )
            )
        await _make_admin(async_client, "wave2-admin6@example.com")

        resp = await async_client.get(QUEUE_URL)
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        # Only the fresh row survives; the aged one was auto-rejected.
        assert len(items) == 1
        assert items[0]["user_id"] == str(await _user_id(email_fresh))

        assert not aged_path.exists()
        async with db_manager.session() as session:
            aged = (
                await session.execute(
                    select(SelfieVerification).where(SelfieVerification.user_id == old_user_id)
                )
            ).scalar_one()
            assert aged.status == "rejected"
            assert aged.rejection_reason == "retention_expired"
            assert aged.deleted_at is not None
            user = await session.get(User, old_user_id)
            assert user.verification_status == "rejected"
            event = (
                await session.execute(
                    select(VerificationEvent).where(
                        VerificationEvent.user_id == old_user_id,
                        VerificationEvent.event_type == "VERIFICATION_REJECTED",
                    )
                )
            ).scalar_one()
            assert event.details["reason"] == "retention_expired"
