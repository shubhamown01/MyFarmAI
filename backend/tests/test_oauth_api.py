"""OAuth (E2) API tests — mocked IdP over httpx.MockTransport, zero network.

A real RSA keypair is generated in-test; id_tokens are signed with jwt.encode
and a matching JWKS is served by the fake transport, so the adapter's genuine
signature-verification path is exercised.
"""

from collections.abc import AsyncGenerator
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient, MockTransport, Response
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.identity import AuthenticationAccount
from app.db.models.user import User
from app.db.session import db_manager
from app.factory import create_app
from app.services import oauth as oauth_service

pytestmark = pytest.mark.usefixtures("async_initialized_db")

AUTHORIZE_URL = "/api/v1/auth/oauth/google/authorize"
CALLBACK_URL = "/api/v1/auth/oauth/google/callback"
REDIRECT_URI = "http://localhost:3000/auth/callback"
GOOGLE_CLIENT_ID = "test-google-client-id"
GOOGLE_CLIENT_SECRET = "test-google-secret"
ISSUER = "https://accounts.google.com"
EMAIL = "farmer@example.com"


# -- fake IdP plumbing ---------------------------------------------------------

_RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_JWK = jwt.algorithms.RSAAlgorithm.to_jwk(_RSA_KEY.public_key(), as_dict=True)
_KID = "test-kid-1"


def _id_token(
    *,
    signing_key: Any = None,
    aud: str = GOOGLE_CLIENT_ID,
    iss: str = ISSUER,
    nonce: str | None = None,
    email: str = EMAIL,
    email_verified: Any = True,
) -> str:
    claims = {
        "iss": iss,
        "sub": "google-sub-123",
        "aud": aud,
        "email": email,
        "email_verified": email_verified,
        "nonce": nonce or "unused",  # replaced by callers that know the nonce
    }
    return jwt.encode(claims, signing_key or _RSA_KEY, algorithm="RS256", headers={"kid": _KID})


def _jwks_document() -> dict[str, Any]:
    return {"keys": [{**_JWK, "kid": _KID, "alg": "RS256", "use": "sig"}]}


def _fake_transport(
    *,
    id_token: str,
    token_status: int = 200,
    jwks_status: int = 200,
) -> MockTransport:
    def handler(request: Any) -> Response:
        if request.url.host == "oauth2.googleapis.com":
            if token_status != 200:
                return Response(token_status, json={"error": "server_error"})
            return Response(200, json={"access_token": "x", "id_token": id_token})
        if request.url.host == "www.googleapis.com":
            return Response(jwks_status, json=_jwks_document())
        return Response(404, json={"error": "unexpected fake-IdP request"})

    return MockTransport(handler)


def _patch_http(monkeypatch: pytest.MonkeyPatch, transport: MockTransport) -> None:
    def fake_client() -> AsyncClient:
        return AsyncClient(transport=transport, base_url="https://fake")

    monkeypatch.setattr(oauth_service, "_make_client", fake_client)


@pytest.fixture
def oauth_app(async_initialized_db: Any) -> Any:
    settings = async_initialized_db.model_copy(
        update={
            "oauth_google_client_id": GOOGLE_CLIENT_ID,
            "oauth_google_client_secret": GOOGLE_CLIENT_SECRET,
        }
    )
    return create_app(settings, test_mode=True)


@pytest.fixture
async def oauth_client(oauth_app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=oauth_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _start_flow(client: AsyncClient) -> tuple[str, str]:
    """Call authorize; returns (state, nonce)."""
    resp = await client.get(AUTHORIZE_URL, params={"redirect_uri": REDIRECT_URI})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "state=" in body["authorize_url"] and "nonce=" in body["authorize_url"]
    assert body["authorize_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert f"client_id={GOOGLE_CLIENT_ID}" in body["authorize_url"]
    # Recover the nonce the service stored (needed to build a valid id_token).
    state = body["state"]
    nonce = oauth_service._oauth_states[state][0]
    return state, nonce


async def _make_active_user(email: str) -> None:
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("Existing-pass-1!")))
        await session.commit()


# -- tests ----------------------------------------------------------------------


class TestOAuthAuthorize:
    async def test_authorize_url_fields(self, oauth_client: AsyncClient) -> None:
        resp = await oauth_client.get(AUTHORIZE_URL, params={"redirect_uri": REDIRECT_URI})
        assert resp.status_code == 200, resp.text
        assert "response_type=code" in resp.json()["authorize_url"]

    async def test_unconfigured_provider_503(self, async_client: AsyncClient) -> None:
        resp = await async_client.get(AUTHORIZE_URL, params={"redirect_uri": REDIRECT_URI})
        assert resp.status_code == 503, resp.text
        assert resp.json()["error_code"] == "OAUTH_NOT_CONFIGURED"

    async def test_unknown_provider_503(self, oauth_client: AsyncClient) -> None:
        resp = await oauth_client.get(
            "/api/v1/auth/oauth/unknown/authorize", params={"redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 503, resp.text


class TestOAuthCallback:
    async def test_happy_first_login_creates_user_and_session(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(
            monkeypatch,
            _fake_transport(id_token=_id_token(nonce=nonce)),
        )
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "authcode", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 200, resp.text
        assert "myfarmai_session=" in resp.headers.get("set-cookie", "")

        me = await oauth_client.get("/api/v1/auth/me")
        assert me.status_code == 200, me.text
        assert me.json()["email"] == EMAIL
        assert me.json()["is_active"] is True

        async with db_manager.session() as session:
            user = (await session.execute(select(User).where(User.email == EMAIL))).scalar_one()
            assert user.is_active and user.email_verified
            assert user.verification_status == "pending_verification"  # E3 self-signup
            links = (
                (
                    await session.execute(
                        select(AuthenticationAccount).where(
                            AuthenticationAccount.user_id == user.id
                        )
                    )
                )
                .scalars()
                .all()
            )
        assert len(links) == 1

    async def test_repeat_login_same_subject_same_user(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce)))
        first = await oauth_client.get(
            CALLBACK_URL, params={"code": "c1", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert first.status_code == 200, first.text
        first_id = first.json()["user"]["id"]

        state2, nonce2 = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce2)))
        second = await oauth_client.get(
            CALLBACK_URL, params={"code": "c2", "state": state2, "redirect_uri": REDIRECT_URI}
        )
        assert second.status_code == 200, second.text
        assert second.json()["user"]["id"] == first_id

    async def test_email_taken_no_linking(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        await _make_active_user(EMAIL)
        state, nonce = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce)))
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "OAUTH_EMAIL_TAKEN"

        async with db_manager.session() as session:
            links = (await session.execute(select(AuthenticationAccount))).scalars().all()
        assert links == []  # never silently merged

    async def test_pending_user_claimed(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Create a pending (inactive, unverified) user the way E1 does.
        async with db_manager.session() as session:
            session.add(
                User(
                    email=EMAIL,
                    password_hash=hash_password("pending-random-password"),
                    is_active=False,
                    email_verified=False,
                )
            )
            await session.commit()

        state, nonce = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce)))
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["user"]["email"] == EMAIL

        async with db_manager.session() as session:
            user = (await session.execute(select(User).where(User.email == EMAIL))).scalar_one()
            assert user.is_active and user.email_verified
            assert user.verification_status == "pending_verification"  # E3 self-signup

    async def test_tampered_signature_invalid_token(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        state, nonce = await _start_flow(oauth_client)
        _patch_http(
            monkeypatch,
            _fake_transport(id_token=_id_token(nonce=nonce, signing_key=other_key)),
        )
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OAUTH_INVALID_TOKEN"

    async def test_wrong_audience_invalid_token(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(
            monkeypatch,
            _fake_transport(id_token=_id_token(nonce=nonce, aud="someone-else")),
        )
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OAUTH_INVALID_TOKEN"

    async def test_wrong_nonce_invalid_token(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(
            monkeypatch,
            _fake_transport(id_token=_id_token(nonce="attacker-chosen-nonce")),
        )
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OAUTH_INVALID_TOKEN"

    async def test_unknown_state_invalid_state(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token()))
        resp = await oauth_client.get(
            CALLBACK_URL,
            params={"code": "c", "state": "never-issued", "redirect_uri": REDIRECT_URI},
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OAUTH_INVALID_STATE"

    async def test_state_single_use_replay(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce)))
        first = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert first.status_code == 200, first.text
        replay = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert replay.status_code == 422, replay.text
        assert replay.json()["error_code"] == "OAUTH_INVALID_STATE"

    async def test_token_endpoint_500(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(monkeypatch, _fake_transport(id_token=_id_token(nonce=nonce), token_status=500))
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 502, resp.text
        assert resp.json()["error_code"] == "OAUTH_TOKEN_EXCHANGE_FAILED"

    async def test_expired_or_malformed_id_token(
        self, oauth_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        state, nonce = await _start_flow(oauth_client)
        _patch_http(
            monkeypatch,
            _fake_transport(id_token="not-a-jwt"),
        )
        resp = await oauth_client.get(
            CALLBACK_URL, params={"code": "c", "state": state, "redirect_uri": REDIRECT_URI}
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "OAUTH_INVALID_TOKEN"


class TestOAuthMicrosoft:
    async def test_microsoft_endpoints_and_issuers(self, async_initialized_db: Any) -> None:
        """Microsoft endpoints are wired with tenant-varying iss accepted."""
        settings = async_initialized_db.model_copy(
            update={
                "oauth_microsoft_client_id": "ms-id",
                "oauth_microsoft_client_secret": "ms-secret",
            }
        )
        provider = oauth_service.get_oauth_provider("microsoft", settings)
        assert provider is not None
        assert provider.authorize_url.startswith("https://login.microsoftonline.com/")
        assert oauth_service._iss_valid(provider, "https://login.microsoftonline.com/tenant-1/v2.0")
        assert not oauth_service._iss_valid(provider, "https://evil.example.com/v2.0")
        assert not oauth_service._iss_valid(
            provider, "https://login.microsoftonline.com/t/wrong-suffix"
        )
