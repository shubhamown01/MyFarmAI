"""AuthService integration tests (P3-04) — hermetic, disposable SQLite (ADR-013)."""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.config import Settings
from app.core.security import hash_token
from app.db.models.audit import AuditEvent, AuditEventType
from app.db.models.user import User, UserRole
from app.db.session import db_manager
from app.services.auth import (
    AuthService,
    InvalidCredentialsError,
    RefreshTokenInvalidError,
    SessionInvalidError,
)


@pytest.fixture(scope="function")
def auth_settings(temp_db_path: str) -> Settings:
    return Settings(
        environment="test",
        database_path=f"sqlite+aiosqlite:///{temp_db_path}",
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        rate_limit_requests=1000,
        log_level="WARNING",
        session_ttl_hours=24,
        session_idle_minutes=120,
        refresh_token_ttl_days=30,
        access_token_ttl_minutes=15,
    )


@pytest_asyncio.fixture()
async def auth_svc(auth_settings: Settings):
    db_manager.initialize(auth_settings.database_path, async_mode=True)
    try:
        # Create tables for the temp DB (models registered via Base metadata).
        from app.db.models.base import Base

        async with db_manager._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with db_manager.session() as session:
            yield AuthService(session, auth_settings)
    finally:
        await db_manager.close()


async def _create_user(svc: AuthService, email: str, password: str) -> User:
    return await svc.create_user(email, password)


pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_success_web(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "farmer@example.com", "S3cure-pass!")
        user, session_id, refresh = await auth_svc.login_password(
            "farmer@example.com", "S3cure-pass!", client_ip="127.0.0.1"
        )
        assert user.email == "farmer@example.com"
        assert len(session_id) >= 43
        assert refresh is None  # web login has no refresh token
        # Only the hash is stored.
        stored = await auth_svc._sessions.get_by_hash(hash_token(session_id))
        assert stored is not None
        assert stored.session_id_hash != session_id

    async def test_login_success_android_gets_refresh(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "a@example.com", "S3cure-pass!")
        _, session_id, refresh = await auth_svc.login_password(
            "a@example.com", "S3cure-pass!", android=True
        )
        assert refresh is not None
        assert len(refresh) >= 43

    async def test_unknown_email_generic_error(self, auth_svc: AuthService) -> None:
        with pytest.raises(InvalidCredentialsError):
            await auth_svc.login_password("nobody@example.com", "pw123456")

    async def test_wrong_password_generic_error(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "b@example.com", "S3cure-pass!")
        with pytest.raises(InvalidCredentialsError):
            await auth_svc.login_password("b@example.com", "wrong-password")

    async def test_deactivated_user_rejected(self, auth_svc: AuthService) -> None:
        user = await _create_user(auth_svc, "c@example.com", "S3cure-pass!")
        await auth_svc._users.deactivate(user.id)
        with pytest.raises(InvalidCredentialsError):
            await auth_svc.login_password("c@example.com", "S3cure-pass!")

    async def test_failed_login_audited_without_password(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "d@example.com", "S3cure-pass!")
        with pytest.raises(InvalidCredentialsError):
            await auth_svc.login_password("d@example.com", "wrong-password")
        result = await auth_svc._session.execute(
            select(AuditEvent).where(AuditEvent.event_type == AuditEventType.LOGIN_FAILED)
        )
        events = result.scalars().all()
        assert len(events) == 1
        assert "S3cure" not in (events[0].description or "")
        assert "wrong-password" not in (events[0].description or "")


class TestSessionValidation:
    async def test_validate_returns_user(self, auth_svc: AuthService) -> None:
        created = await _create_user(auth_svc, "e@example.com", "S3cure-pass!")
        _, session_id, _ = await auth_svc.login_password("e@example.com", "S3cure-pass!")
        user = await auth_svc.validate_session(session_id)
        assert user.id == created.id

    async def test_invalid_session_rejected(self, auth_svc: AuthService) -> None:
        with pytest.raises(SessionInvalidError):
            await auth_svc.validate_session("forged-session-id-0000000000000000000000")

    async def test_expired_session_rejected(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "f@example.com", "S3cure-pass!")
        _, session_id, _ = await auth_svc.login_password("f@example.com", "S3cure-pass!")
        stored = await auth_svc._sessions.get_by_hash(hash_token(session_id))
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        with pytest.raises(SessionInvalidError):
            await auth_svc.validate_session(session_id)

    async def test_revoked_session_rejected(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "g@example.com", "S3cure-pass!")
        _, session_id, _ = await auth_svc.login_password("g@example.com", "S3cure-pass!")
        await auth_svc._sessions.revoke(hash_token(session_id), reason="test")
        with pytest.raises(SessionInvalidError):
            await auth_svc.validate_session(session_id)

    async def test_logout_revokes_session(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "h@example.com", "S3cure-pass!")
        _, session_id, _ = await auth_svc.login_password("h@example.com", "S3cure-pass!")
        assert await auth_svc.logout(session_id) is True
        with pytest.raises(SessionInvalidError):
            await auth_svc.validate_session(session_id)
        assert await auth_svc.logout(session_id) is False


class TestRefreshRotation:
    async def test_rotation_issues_new_pair(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "i@example.com", "S3cure-pass!")
        _, old_session, old_refresh = await auth_svc.login_password(
            "i@example.com", "S3cure-pass!", android=True
        )
        user, new_session, new_refresh = await auth_svc.rotate_refresh(old_refresh)
        assert user.email == "i@example.com"
        assert new_refresh != old_refresh
        assert new_session != old_session

    async def test_old_refresh_single_use(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "j@example.com", "S3cure-pass!")
        _, _, old_refresh = await auth_svc.login_password(
            "j@example.com", "S3cure-pass!", android=True
        )
        _, _, new_refresh = await auth_svc.rotate_refresh(old_refresh)
        with pytest.raises(RefreshTokenInvalidError):
            await auth_svc.rotate_refresh(old_refresh)

    async def test_reuse_revokes_all_sessions(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "k@example.com", "S3cure-pass!")
        _, session_a, old_refresh = await auth_svc.login_password(
            "k@example.com", "S3cure-pass!", android=True
        )
        _, session_b, new_refresh = await auth_svc.rotate_refresh(old_refresh)
        # Replaying the rotated-out token must kill everything.
        with pytest.raises(RefreshTokenInvalidError):
            await auth_svc.rotate_refresh(old_refresh)
        for sid in (session_a, session_b, new_refresh):
            with pytest.raises(SessionInvalidError):
                await auth_svc.validate_session(sid)

    async def test_garbage_refresh_rejected(self, auth_svc: AuthService) -> None:
        with pytest.raises(RefreshTokenInvalidError):
            await auth_svc.rotate_refresh("not-a-real-token-000000000000000")


class TestUserCreation:
    async def test_create_user_hashes_password(self, auth_svc: AuthService) -> None:
        user = await _create_user(auth_svc, "l@example.com", "S3cure-pass!")
        assert user.password_hash.startswith("$argon2id$")
        assert user.role == UserRole.USER

    async def test_duplicate_email_rejected(self, auth_svc: AuthService) -> None:
        await _create_user(auth_svc, "m@example.com", "S3cure-pass!")
        with pytest.raises(ValueError):
            await _create_user(auth_svc, "m@example.com", "other-password")
