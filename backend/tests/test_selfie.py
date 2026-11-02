"""Selfie liveness verification tests (E3 wave 1) — async mode (aiosqlite)."""

import io
import os
import time
import uuid
from collections import defaultdict

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select

from app.db.models.identity import SelfieVerification
from app.db.models.user import User
from app.db.session import db_manager
from app.services import selfie as selfie_service
from app.services.delivery import DevModeEmailDelivery

pytestmark = pytest.mark.usefixtures("async_initialized_db")

REQUEST_URL = "/api/v1/auth/register/email/request-otp"
VERIFY_URL = "/api/v1/auth/register/email/verify"
CONSENT_URL = "/api/v1/verification/selfie/consent"
CHALLENGE_URL = "/api/v1/verification/selfie/challenge"
UPLOAD_URL = "/api/v1/verification/selfie/upload"


# -- helpers ------------------------------------------------------------------


def _capture_deliveries(monkeypatch: pytest.MonkeyPatch) -> defaultdict[str, list[str]]:
    captured: defaultdict[str, list[str]] = defaultdict(list)

    async def fake_send_otp(self, destination: str, code: str) -> None:
        captured[destination].append(code)

    monkeypatch.setattr(DevModeEmailDelivery, "send_otp", fake_send_otp)
    return captured


async def _signup_pending_user(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, email: str
) -> str:
    """Run the email-OTP flow: leaves the client logged in as a user whose
    verification_status is 'pending_verification' (E3 activation semantics)."""
    captured = _capture_deliveries(monkeypatch)
    await client.post(REQUEST_URL, json={"email": email})
    code = captured[email][0]
    resp = await client.post(VERIFY_URL, json={"email": email, "code": code})
    assert resp.status_code == 200, resp.text
    return email


async def _user_id(email: str) -> uuid.UUID:
    async with db_manager.session() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        return user.id


def _jpeg(width: int = 640, height: int = 640, *, exif: Image.Exif | None = None) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), (90, 140, 90))
    if exif is not None:
        img.save(buf, "JPEG", exif=exif)
    else:
        img.save(buf, "JPEG")
    return buf.getvalue()


@pytest.fixture
def clean_challenges():
    selfie_service._challenges.clear()
    selfie_service._user_latest.clear()
    yield
    selfie_service._challenges.clear()
    selfie_service._user_latest.clear()


@pytest.fixture
def selfie_dir(async_test_settings, tmp_path, monkeypatch):
    """Point the shared settings instance at a per-test storage dir."""
    d = tmp_path / "selfies"
    monkeypatch.setattr(async_test_settings, "selfie_storage_dir", str(d))
    return d


# -- tests --------------------------------------------------------------------


class TestSelfieVerification:
    async def test_endpoints_require_auth(self, async_client: AsyncClient) -> None:
        for url in (CONSENT_URL, CHALLENGE_URL, UPLOAD_URL):
            resp = await async_client.post(url)
            assert resp.status_code == 401, (url, resp.text)

    async def test_consent_granted(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _signup_pending_user(async_client, monkeypatch, "e3-consent@verifytest.com")
        resp = await async_client.post(CONSENT_URL)
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"status": "granted"}

    async def test_challenge_without_consent_conflict(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _signup_pending_user(async_client, monkeypatch, "e3-noconsent@verifytest.com")
        resp = await async_client.post(CHALLENGE_URL)
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "CONSENT_REQUIRED"

    async def test_challenge_two_distinct_actions(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch, clean_challenges
    ) -> None:
        email = "e3-challenge@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email)
        assert (await async_client.post(CONSENT_URL)).status_code == 200

        resp = await async_client.post(CHALLENGE_URL)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["expires_in"] == 300
        assert len(body["actions"]) == 2
        assert len(set(body["actions"])) == 2
        assert all(a in selfie_service.ACTIONS for a in body["actions"])

    async def _happy_flow(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        email: str,
        data: bytes,
        filename: str = "selfie.jpg",
    ):
        await _signup_pending_user(async_client, monkeypatch, email)
        assert (await async_client.post(CONSENT_URL)).status_code == 200
        challenge = (await async_client.post(CHALLENGE_URL)).json()
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": (filename, data, "image/jpeg")},
            data={"challenge_id": challenge["challenge_id"]},
        )
        return challenge, resp

    async def test_upload_happy_path(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-happy@verifytest.com"
        challenge, resp = await self._happy_flow(async_client, monkeypatch, email, _jpeg())
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body == {"status": "received", "review_state": "pending_review"}
        # No storage path/URL/filename anywhere in the response.
        assert "path" not in body and "url" not in body and "file" not in body

        async with db_manager.session() as session:
            row = (
                await session.execute(
                    select(SelfieVerification).where(
                        SelfieVerification.user_id == await _user_id(email)
                    )
                )
            ).scalar_one()
            assert row.status == "pending_review"
            assert row.challenge_completed is True
            path = row.storage_path

        stored = selfie_dir / os.path.basename(path)
        assert stored.is_file() and str(stored) == path
        assert (os.stat(stored).st_mode & 0o777) == 0o600

        # No auto-approval: user stays pending, session still works.
        async with db_manager.session() as session:
            user = (await session.execute(select(User).where(User.email == email))).scalar_one()
            assert user.verification_status == "pending_verification"
            assert user.is_active is True
        me = await async_client.get("/api/v1/auth/me")
        assert me.status_code == 200, me.text

    async def test_challenge_replay_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-replay@verifytest.com"
        challenge, _ = await self._happy_flow(async_client, monkeypatch, email, _jpeg())
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("again.jpg", _jpeg(), "image/jpeg")},
            data={"challenge_id": challenge["challenge_id"]},
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "CHALLENGE_INVALID"

    async def test_expired_challenge_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-expired@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email)
        await async_client.post(CONSENT_URL)
        cid = (await async_client.post(CHALLENGE_URL)).json()["challenge_id"]
        # Backdate the in-memory store entry past its TTL.
        entry = selfie_service._challenges[cid]
        selfie_service._challenges[cid] = (entry[0], time.monotonic() - 1, entry[2])

        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("s.jpg", _jpeg(), "image/jpeg")},
            data={"challenge_id": cid},
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "CHALLENGE_INVALID"

    async def test_wrong_user_challenge_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email_a = "e3-owner@verifytest.com"
        email_b = "e3-thief@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email_a)
        await async_client.post(CONSENT_URL)
        cid = (await async_client.post(CHALLENGE_URL)).json()["challenge_id"]

        await _signup_pending_user(async_client, monkeypatch, email_b)
        await async_client.post(CONSENT_URL)
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("s.jpg", _jpeg(), "image/jpeg")},
            data={"challenge_id": cid},
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "CHALLENGE_INVALID"

    async def test_garbage_bytes_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-garbage@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email)
        await async_client.post(CONSENT_URL)
        cid = (await async_client.post(CHALLENGE_URL)).json()["challenge_id"]
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("s.jpg", b"definitely not an image" * 100, "image/jpeg")},
            data={"challenge_id": cid},
        )
        assert resp.status_code == 415, resp.text
        assert resp.json()["error_code"] == "UNSUPPORTED_MEDIA_TYPE"

    async def test_oversize_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-big@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email)
        await async_client.post(CONSENT_URL)
        cid = (await async_client.post(CHALLENGE_URL)).json()["challenge_id"]
        data = b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024)
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("s.jpg", data, "image/jpeg")},
            data={"challenge_id": cid},
        )
        assert resp.status_code == 413, resp.text
        # The global body-size middleware usually intercepts first
        # (REQUEST_BODY_TOO_LARGE); IMAGE_TOO_LARGE only for bodies under it.
        assert resp.json()["error_code"] in ("REQUEST_BODY_TOO_LARGE", "IMAGE_TOO_LARGE")

    async def test_undersized_image_rejected(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-small@verifytest.com"
        await _signup_pending_user(async_client, monkeypatch, email)
        await async_client.post(CONSENT_URL)
        cid = (await async_client.post(CHALLENGE_URL)).json()["challenge_id"]
        resp = await async_client.post(
            UPLOAD_URL,
            files={"file": ("s.jpg", _jpeg(300, 300), "image/jpeg")},
            data={"challenge_id": cid},
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "IMAGE_DIMENSIONS"

    async def test_exif_stripped(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
        clean_challenges,
        selfie_dir,
    ) -> None:
        email = "e3-exif@verifytest.com"
        exif = Image.Exif()
        exif[0x010F] = "SecretCamMaker"  # Make tag
        exif[0x0110] = "SecretCamModel"  # Model tag
        challenge, resp = await self._happy_flow(async_client, monkeypatch, email, _jpeg(exif=exif))
        assert resp.status_code == 200, resp.text

        async with db_manager.session() as session:
            row = (
                await session.execute(
                    select(SelfieVerification).where(
                        SelfieVerification.user_id == await _user_id(email)
                    )
                )
            ).scalar_one()
        with Image.open(row.storage_path) as clean:
            assert clean.getexif() == {}  # all camera metadata stripped
