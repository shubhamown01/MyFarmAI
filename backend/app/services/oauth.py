"""OAuth OIDC adapters (E2 — Google/Microsoft authorization-code flow).

Per directive §4.1: validates issuer, audience, signature (JWKS), nonce, and
state. Sessions are established through the existing
``AuthService._establish_session`` path (same web HttpOnly cookie as password
login and email-OTP verification).

STATE HANDLING (single-process limitation): ``Settings`` exposes no signing
secret, so OAuth ``state``/``nonce`` pairs are kept in a module-level
in-memory store with a 10-minute TTL and single-use consumption. This is
safe for the approved single-process deployment; a multi-worker/replica
deployment must move this to shared storage (Redis/DB) first.

Providers are ENABLED only when both client id and secret are configured
(env-based). Unconfigured providers return 503 OAUTH_NOT_CONFIGURED — live
verification is deferred until the owner creates the Google/Microsoft apps.

All outbound HTTP goes through an injectable ``httpx.AsyncClient`` (tests
pass a ``MockTransport``-backed fake; zero network).
"""

import json
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.identity import AuthenticationAccount
from app.db.models.user import User
from app.services.auth import AuthService

STATE_TTL_SECONDS = 600
JWKS_CACHE_TTL_SECONDS = 3600
HTTP_TIMEOUT_SECONDS = 10.0
OAUTH_SCOPE = "openid email profile"


class OAuthNotConfiguredError(Exception):
    """Provider has no client id/secret configured (env)."""


class OAuthInvalidStateError(Exception):
    """State missing, expired, already consumed, or replayed."""


class OAuthTokenExchangeError(Exception):
    """Token endpoint returned an error or unusable response."""


class OAuthInvalidTokenError(Exception):
    """id_token failed signature/audience/issuer/nonce/expiry validation."""


class OAuthEmailTakenError(Exception):
    """Provider email belongs to an existing ACTIVE account — never auto-link."""


class OAuthProviderError(Exception):
    """Unexpected provider-side failure."""


@dataclass(frozen=True)
class OAuthProvider:
    """Static endpoints + credentials for one OAuth provider."""

    name: str
    authorize_url: str
    token_url: str
    jwks_url: str
    client_id: str
    client_secret: str
    scope: str
    # Exact iss values accepted (Google). Microsoft uses tenant-varying iss.
    issuers: tuple[str, ...]


_GOOGLE = {
    "name": "google",
    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
    "issuers": ("https://accounts.google.com",),
}
_MICROSOFT = {
    "name": "microsoft",
    "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
    "jwks_url": "https://login.microsoftonline.com/common/discovery/v2.0/keys",
    "issuers": (),  # tenant-varying; validated by predicate below
}


def get_oauth_provider(name: str, settings: Settings) -> OAuthProvider | None:
    """Build the provider config, or None when unconfigured/unknown."""
    name = name.strip().lower()
    if name == "google":
        base, cid, csec = (
            _GOOGLE,
            settings.oauth_google_client_id,
            settings.oauth_google_client_secret,
        )
    elif name == "microsoft":
        base, cid, csec = (
            _MICROSOFT,
            settings.oauth_microsoft_client_id,
            settings.oauth_microsoft_client_secret,
        )
    else:
        return None
    if not cid or not csec:
        return None
    return OAuthProvider(
        name=str(base["name"]),
        authorize_url=str(base["authorize_url"]),
        token_url=str(base["token_url"]),
        jwks_url=str(base["jwks_url"]),
        client_id=cid,
        client_secret=csec,
        scope=OAUTH_SCOPE,
        issuers=tuple(base["issuers"]),  # type: ignore[arg-type]
    )


def _iss_valid(provider: OAuthProvider, iss: str) -> bool:
    if provider.name == "microsoft":
        return iss.startswith("https://login.microsoftonline.com/") and iss.endswith("/v2.0")
    return iss in provider.issuers


# -- state store (single-process; see module docstring) ----------------------

_oauth_states: dict[str, tuple[str, float]] = {}  # state -> (nonce, expiry monotonic)


def _prune_expired_states() -> None:
    now = time.monotonic()
    for key in [k for k, (_, exp) in _oauth_states.items() if exp <= now]:
        del _oauth_states[key]


def store_oauth_state(state: str, nonce: str) -> None:
    """Record a pending state/nonce pair (bounded by TTL pruning)."""
    _prune_expired_states()
    _oauth_states[state] = (nonce, time.monotonic() + STATE_TTL_SECONDS)


def consume_oauth_state(state: str) -> str:
    """Single-use pop; returns the nonce or raises OAuthInvalidStateError."""
    entry = _oauth_states.pop(state, None)
    if entry is None or time.monotonic() > entry[1]:
        raise OAuthInvalidStateError("unknown, expired, or replayed state")
    return entry[0]


# -- flow --------------------------------------------------------------------


def _make_client() -> httpx.AsyncClient:
    """Build the outbound HTTP client (monkeypatched by tests)."""
    return httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)


def build_authorize_url(provider: OAuthProvider, redirect_uri: str) -> tuple[str, str]:
    """Generate state+nonce, record them, and return (authorize_url, state)."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    store_oauth_state(state, nonce)
    params = {
        "response_type": "code",
        "client_id": provider.client_id,
        "redirect_uri": redirect_uri,
        "scope": provider.scope,
        "state": state,
        "nonce": nonce,
    }
    return f"{provider.authorize_url}?{urlencode(params)}", state


_jwks_cache: dict[str, tuple[float, dict[str, Any]]] = {}  # jwks_url -> (expiry, doc)


async def _fetch_jwks(provider: OAuthProvider, client: httpx.AsyncClient) -> dict[str, Any]:
    cached = _jwks_cache.get(provider.jwks_url)
    if cached is not None and time.monotonic() < cached[0]:
        return cached[1]
    resp = await client.get(provider.jwks_url)
    if resp.status_code != 200:
        raise OAuthProviderError(f"JWKS fetch failed with HTTP {resp.status_code}")
    doc: dict[str, Any] = resp.json()
    _jwks_cache[provider.jwks_url] = (time.monotonic() + JWKS_CACHE_TTL_SECONDS, doc)
    return doc


async def exchange_and_verify(
    provider: OAuthProvider,
    code: str,
    redirect_uri: str,
    expected_nonce: str,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, str]:
    """Exchange the code and verify the id_token (directive §4.1).

    Returns {"provider", "subject", "email"}. Raises OAuthTokenExchangeError
    (token endpoint failure), OAuthInvalidTokenError (any claim validation
    failure), or OAuthProviderError (JWKS/transport problems).
    """
    if http_client is None:
        client = _make_client()
        try:
            return await exchange_and_verify(
                provider, code, redirect_uri, expected_nonce, http_client=client
            )
        finally:
            await client.aclose()

    client = http_client
    resp = await client.post(
        provider.token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        },
        headers={"Accept": "application/json"},
    )
    if resp.status_code != 200:
        raise OAuthTokenExchangeError(f"token endpoint returned HTTP {resp.status_code}")
    token_data = resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        raise OAuthTokenExchangeError("token response missing id_token")

    try:
        header = jwt.get_unverified_header(id_token)
    except jwt.PyJWTError as exc:
        raise OAuthInvalidTokenError("malformed id_token") from exc
    kid = header.get("kid")
    if not kid:
        raise OAuthInvalidTokenError("id_token missing kid")

    jwks = await _fetch_jwks(provider, client)
    keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
    if not keys:
        raise OAuthInvalidTokenError("no matching JWKS key")
    try:
        public_key = RSAAlgorithm.from_jwk(json.dumps(keys[0]))
        verified: dict[str, Any] = jwt.decode(
            id_token,
            key=public_key,
            algorithms=["RS256"],
            audience=provider.client_id,
            options={"verify_iss": False},  # issuer validated below (tenant-varying)
        )
    except jwt.PyJWTError as exc:
        raise OAuthInvalidTokenError(f"id_token validation failed: {exc}") from exc

    if not _iss_valid(provider, verified.get("iss", "")):
        raise OAuthInvalidTokenError("unexpected issuer")
    if verified.get("nonce") != expected_nonce:
        raise OAuthInvalidTokenError("nonce mismatch")
    subject = verified.get("sub")
    email = verified.get("email") or verified.get("preferred_username")
    if not subject or not email:
        raise OAuthInvalidTokenError("id_token missing subject or email")
    # Provider-issued email is trusted (google email_verified claim honored
    # when present-and-false only).
    if verified.get("email_verified") is False:
        raise OAuthInvalidTokenError("email not verified by provider")
    return {"provider": provider.name, "subject": str(subject), "email": str(email).lower()}


async def login_or_signup_oauth(
    session: AsyncSession,
    claims: dict[str, str],
    settings: Settings,
    *,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[User, str]:
    """Resolve/link the identity and open a web session (account-linking
    protection per directive: NEVER silently merge into an active account).

    Returns (user, session_id). Outcomes audited by _establish_session
    (LOGIN_SUCCESS) exactly as in the password/OTP paths.
    """
    provider_name = claims["provider"]
    subject = claims["subject"]
    email = claims["email"]

    account = (
        await session.execute(
            select(AuthenticationAccount)
            .where(AuthenticationAccount.provider == provider_name)
            .where(AuthenticationAccount.provider_account_id == subject)
        )
    ).scalar_one_or_none()
    if account is not None:
        user = await session.get(User, account.user_id)
        if user is None or not user.is_active:
            raise OAuthInvalidTokenError("linked account is disabled")
    else:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if user is not None:
            # Claimable = email control already proven or not required yet:
            #  - inactive (pre-activation E1 signup), OR
            #  - pending_verification (E1 OTP-verified, awaiting the E3 selfie
            #    gate). The provider-verified email matches the account's
            #    identity; linking adds the provider row without touching
            #    other credentials.
            claimable = not user.is_active or user.verification_status == "pending_verification"
            if not claimable:
                # Account-takeover protection: ACTIVE accounts with a real
                # lifecycle status (active/rejected) are never linked.
                raise OAuthEmailTakenError(
                    "email already registered; log in with your existing method"
                )
            # PENDING email-OTP user: safe to claim — provider-verified email.
            user.is_active = True
            user.email_verified = True
            user.verification_status = "pending_verification"  # E3: self-signup
        else:
            user = User(
                email=email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                is_active=True,
                email_verified=True,
                verification_status="pending_verification",  # E3: self-signup
            )
            session.add(user)
            await session.flush()
        session.add(
            AuthenticationAccount(
                user_id=user.id, provider=provider_name, provider_account_id=subject
            )
        )
        await session.flush()

    session_id, _ = await AuthService(session, settings)._establish_session(
        user, client_ip=client_ip, user_agent=user_agent, android=False
    )
    return user, session_id
