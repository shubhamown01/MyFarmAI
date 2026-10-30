"""Authentication service (ADR-008): opaque sessions, Argon2id, rotation.

Design notes:
- Web sessions and Android access tokens both use the hashed-opaque ``Session``
  model; Android access tokens simply get a shorter TTL (``access_token_ttl_minutes``).
- Only SHA-256 hashes of session IDs / refresh tokens are stored (ADR-008).
- Refresh tokens rotate single-use with ``parent_token_hash`` lineage; presenting
  a revoked token revokes the whole chain and all the user's sessions (reuse
  detection).
- Errors are generic — never disclose whether an account exists.
"""

import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    generate_refresh_token,
    generate_session_id,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from app.db.models.audit import AuditEventType
from app.db.models.user import User, UserRole
from app.db.repositories import (
    AuditRepository,
    RefreshTokenRepository,
    SessionRepository,
    UserRepository,
)


class InvalidCredentialsError(Exception):
    """Generic login failure — identical for unknown email and wrong password."""


class SessionInvalidError(Exception):
    """Session missing, expired, revoked, or user deactivated."""


class RefreshTokenInvalidError(Exception):
    """Refresh token invalid, expired, or reused."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(dt: datetime) -> datetime:
    """Normalize DB datetimes: SQLite returns naive UTC, PG returns aware."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


# Per-account failed-login tracking (process-local; P3-11).
# Keyed by lowercased email; values are failure timestamps (monotonic).
_FAILED_LOGINS: dict[str, list[float]] = defaultdict(list)
_FAILED_LOGIN_LIMIT = 5
_FAILED_LOGIN_WINDOW_SECONDS = 15 * 60


class AccountLockedError(Exception):
    """Too many failed logins for this account within the window."""


def _record_failed_login(email: str) -> None:
    now = time.monotonic()
    bucket = _FAILED_LOGINS[email.strip().lower()]
    bucket[:] = [t for t in bucket if now - t < _FAILED_LOGIN_WINDOW_SECONDS]
    bucket.append(now)
    # Bounded memory (exit-gate fix): evict empty/stale buckets when oversized.
    if len(_FAILED_LOGINS) > 10_000:
        for key in [k for k, v in _FAILED_LOGINS.items() if not v][:5_000]:
            del _FAILED_LOGINS[key]


def _account_locked(email: str) -> bool:
    now = time.monotonic()
    bucket = _FAILED_LOGINS[email.strip().lower()]
    bucket[:] = [t for t in bucket if now - t < _FAILED_LOGIN_WINDOW_SECONDS]
    return len(bucket) >= _FAILED_LOGIN_LIMIT


def _clear_failed_logins(email: str) -> None:
    _FAILED_LOGINS.pop(email.strip().lower(), None)


class AuthService:
    """Authentication lifecycle operations."""

    def __init__(self, session: AsyncSession, settings: Settings):
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._sessions = SessionRepository(session)
        self._refresh = RefreshTokenRepository(session)
        self._audit = AuditRepository(session)

    # -- preferences (P5G) --------------------------------------------------

    async def update_preferences(self, user: User, *, preferred_language: str):
        """Update the authenticated user's own preferences (caller passes the
        session-validated user object)."""
        user.preferred_language = preferred_language
        await self._session.flush()
        return user

    # -- login ------------------------------------------------------------

    async def login_password(
        self,
        email: str,
        password: str,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
        android: bool = False,
    ) -> tuple[User, str, str | None]:
        """Verify credentials and create a session (+ refresh token for Android).

        Returns (user, session_id, refresh_token); refresh_token is None for web.
        Raises InvalidCredentialsError (generic) on any failure.
        """
        if _account_locked(email):
            # Blocked before any DB work: 5 failures within the window lock the account.
            raise AccountLockedError("too many failed logins")
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            _record_failed_login(email)
            raise InvalidCredentialsError("invalid email or password")
        if not verify_password(password, user.password_hash):
            _record_failed_login(email)
            await self._audit.log(
                event_type=AuditEventType.LOGIN_FAILED,
                event_category="security",
                description="Failed login attempt",
                subject_id=user.id,
                subject_type="user",
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
            )
            raise InvalidCredentialsError("invalid email or password")

        _clear_failed_logins(email)

        if needs_rehash(user.password_hash):
            await self._users.update_password_hash(user.id, hash_password(password))

        session_id = generate_session_id()
        ttl = (
            timedelta(minutes=self._settings.access_token_ttl_minutes)
            if android
            else timedelta(hours=self._settings.session_ttl_hours)
        )
        await self._sessions.create(
            user_id=user.id,
            session_id_hash=hash_token(session_id),
            expires_at=_utcnow() + ttl,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        refresh_token: str | None = None
        if android:
            refresh_token = generate_refresh_token()
            await self._refresh.create(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=_utcnow() + timedelta(days=self._settings.refresh_token_ttl_days),
                ip_address=client_ip,
                user_agent=user_agent,
            )

        await self._users.update_last_login(user.id)
        await self._audit.log(
            event_type=AuditEventType.LOGIN_SUCCESS,
            event_category="security",
            description="User logged in",
            actor_id=user.id,
            subject_id=user.id,
            subject_type="user",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        return user, session_id, refresh_token

    # -- session validation -----------------------------------------------

    async def validate_session(self, session_id: str) -> User:
        """Resolve a session ID to its active user, enforcing expiry and idle timeout.

        Touches last-activity (updated_at) on success to slide the idle window.
        Raises SessionInvalidError otherwise.
        """
        session_obj = await self._sessions.get_by_hash(hash_token(session_id))
        if session_obj is None or session_obj.is_revoked:
            raise SessionInvalidError("session invalid")
        now = _utcnow()
        if _aware(session_obj.expires_at) <= now:
            raise SessionInvalidError("session expired")
        idle_limit = _aware(session_obj.updated_at) + timedelta(
            minutes=self._settings.session_idle_minutes
        )
        if idle_limit <= now:
            await self._sessions.revoke(session_obj.session_id_hash, reason="idle_timeout")
            raise SessionInvalidError("session expired")
        user = await self._users.get_by_id(session_obj.user_id)
        if user is None or not user.is_active:
            raise SessionInvalidError("session invalid")
        session_obj.updated_at = now  # slide the idle window
        return user

    # -- logout -----------------------------------------------------------

    async def logout(self, session_id: str, *, client_ip: str | None = None) -> bool:
        """Revoke the presented session. Returns True if it existed."""
        revoked = await self._sessions.revoke(hash_token(session_id), reason="logout")
        if revoked:
            await self._audit.log(
                event_type=AuditEventType.LOGOUT,
                event_category="security",
                description="User logged out",
                ip_address=client_ip,
            )
        return revoked

    # -- refresh rotation ---------------------------------------------------

    async def rotate_refresh(
        self,
        refresh_token: str,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, str, str]:
        """Single-use refresh rotation; returns (user, new_access_session_id, new_refresh_token).

        Reuse of a revoked token revokes the whole chain and every session of
        the user (suspected theft), then raises RefreshTokenInvalidError.
        """
        token_hash = hash_token(refresh_token)
        stored = await self._refresh.get_by_hash(token_hash)
        if stored is None or _aware(stored.expires_at) <= _utcnow():
            raise RefreshTokenInvalidError("refresh token invalid")
        if stored.is_revoked:
            # Reuse detected: revoke EVERY refresh token and session for this
            # user (suspected theft). Chain-walking alone would leave tokens
            # >=2 generations old live (exit-gate finding, FCL-026).
            await self._refresh.revoke_all_user_tokens(
                stored.user_id, reason="refresh_reuse_detected"
            )
            await self._sessions.revoke_all_user_sessions(
                stored.user_id, reason="refresh_reuse_detected"
            )
            await self._audit.log(
                event_type=AuditEventType.REFRESH_TOKEN_REVOKED,
                event_category="security",
                description="Revoked refresh token reused; all user refresh tokens and sessions revoked",
                actor_id=stored.user_id,
                subject_id=stored.user_id,
                subject_type="user",
                ip_address=client_ip,
                user_agent=user_agent,
                success=False,
            )
            # Security revocations must persist even though this request errors
            # (the session CM would otherwise roll them back with the exception).
            await self._session.commit()
            raise RefreshTokenInvalidError("refresh token invalid")

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise RefreshTokenInvalidError("refresh token invalid")

        # Rotate: revoke old, issue a new token in the same chain.
        await self._refresh.revoke(token_hash, reason="rotated")
        new_refresh = generate_refresh_token()
        await self._refresh.create(
            user_id=user.id,
            token_hash=hash_token(new_refresh),
            expires_at=_utcnow() + timedelta(days=self._settings.refresh_token_ttl_days),
            parent_token_hash=token_hash,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        new_session = generate_session_id()
        await self._sessions.create(
            user_id=user.id,
            session_id_hash=hash_token(new_session),
            expires_at=_utcnow() + timedelta(minutes=self._settings.access_token_ttl_minutes),
            ip_address=client_ip,
            user_agent=user_agent,
        )
        return user, new_session, new_refresh

    # -- admin account management ------------------------------------------

    async def create_user(
        self,
        email: str,
        password: str,
        *,
        full_name: str | None = None,
        role: UserRole = UserRole.USER,
        actor_id: uuid.UUID | None = None,
    ) -> User:
        """Create an account (admin-created accounts policy, ADR-008).

        Raises ValueError if the email is already registered (caller maps to a
        generic conflict response without leaking more detail).
        """
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise ValueError("email already registered")
        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        user.role = role
        await self._audit.log(
            event_type=AuditEventType.ACCOUNT_CREATED,
            event_category="security",
            description="Account created by admin",
            actor_id=actor_id,
            subject_id=user.id,
            subject_type="user",
        )
        return user
