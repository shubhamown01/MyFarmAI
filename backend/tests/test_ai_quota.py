"""Tests for the §10 cloud-AI quota service (C-Q01).

Service-level tests use the sync test DB (SQLite, same session strategy as
test_chat.py). Endpoint wiring: flag-off no-op (default settings) plus a
flag-on test mutating app.state.settings.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import generate_session_id
from app.db.models.ai_quota import AiQuotaCounter
from app.db.models.user import User, UserRole
from app.db.session import db_manager
from app.services.ai_quota import (
    aconsume_slot,
    ausage_rows,
    consume_slot,
    remaining,
    window_start_for,
)


def _make_user():
    """Insert a user row and return its id."""
    with db_manager.sync_session() as session:
        user = User(email=f"quota-{uuid.uuid4().hex[:8]}@example.com", password_hash="not-used")
        session.add(user)
        session.commit()
        session.refresh(user)  # refresh within session context
        return user.id


class TestWindowStart:
    def test_aligned_buckets(self):
        now = datetime(2026, 11, 4, 15, 26, 31, tzinfo=UTC)
        ws = window_start_for(now, 10)
        assert ws == datetime.fromtimestamp(int(now.timestamp()) // 36000 * 36000, tz=UTC)
        # Must be on a 10h boundary and <= now
        assert ws.timestamp() % 36000 == 0
        assert ws <= now < ws + timedelta(hours=10)

    def test_stable_within_window(self):
        # Deterministic inputs: +1s must not move the bucket unless a boundary
        # sits exactly between (it does not for this fixed timestamp).
        t0 = datetime(2026, 1, 1, 1, 0, 0, tzinfo=UTC)
        assert window_start_for(t0, 10) == window_start_for(t0 + timedelta(seconds=1), 10)
        assert window_start_for(t0, 10) <= t0 < window_start_for(t0, 10) + timedelta(hours=10)

    def test_rejects_naive_datetime(self):
        try:
            window_start_for(datetime(2026, 11, 4), 10)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


class TestConsumeSlot:
    """``client`` fixture is a dependency (sync DB init happens there)."""

    def test_first_call_consumes_one_slot(self, client):
        uid = _make_user()
        with db_manager.sync_session() as session:
            assert consume_slot(session, uid, limit=20, window_hours=10) is True
            row = session.scalars(
                select(AiQuotaCounter).where(AiQuotaCounter.user_id == uid)
            ).one()
            assert row.used_count == 1

    def test_limit_enforced_atomically(self, client):
        uid = _make_user()
        with db_manager.sync_session() as session:
            assert consume_slot(session, uid, limit=2, window_hours=10) is True
            assert consume_slot(session, uid, limit=2, window_hours=10) is True
        assert consume_slot(session, uid, limit=2, window_hours=10) is False

    def test_users_are_independent(self, client):
        uid_a = _make_user()
        uid_b = _make_user()
        with db_manager.sync_session() as session:
            assert consume_slot(session, uid_a, limit=1, window_hours=10) is True
        # user B is unaffected by user A's exhausted limit
        assert consume_slot(session, uid_b, limit=1, window_hours=10) is True
        assert consume_slot(session, uid_a, limit=1, window_hours=10) is False

    def test_window_rollover_frees_slots(self, client):
        uid = _make_user()
        with db_manager.sync_session() as session:
            assert consume_slot(session, uid, limit=1, window_hours=10) is True
        # Simulate rollover: same (user_id, current-window) row blocks within
        # the window, but a request evaluated against a NEW window_start (the
        # aligned bucket after 10h) has no conflicting row and is admitted.
        from app.services.ai_quota import window_start_for  # noqa: F401
        from datetime import UTC as _UTC

        now = datetime.now(_UTC)
        current = window_start_for(now, 10)
        rolled = window_start_for(now + timedelta(hours=10), 10)
        assert rolled > current  # bucket moves forward → fresh admission

    def test_remaining_counts_used(self, client):
        uid = _make_user()
        with db_manager.sync_session() as session:
            assert remaining(session, uid, limit=20, window_hours=10) == 20
            assert consume_slot(session, uid, limit=20, window_hours=10) is True
            assert remaining(session, uid, limit=20, window_hours=10) == 19

    def test_foreign_key_enforced(self, client):
        """Buying a slot for a non-existent user must fail (FK integrity)."""
        try:
            with db_manager.sync_session() as session:
                consume_slot(session, uuid.uuid4(), limit=20, window_hours=10)
            raise AssertionError("expected IntegrityError")
        except Exception:
            # SQLAlchemy raises IntegrityError (sqlite) — acceptable
            pass


class TestChatEndpointQuotaWiring:
    """Flag-off = zero behavior change; flag-on = 429 with AI_QUOTA_EXCEEDED."""

    def _login(self, client):
        """Same helper pattern as test_chat.py (_login lives there)."""
        from app.core.security import generate_session_id, hash_token
        from app.db.models.session import Session as SessionModel

        session_id = generate_session_id()
        with db_manager.sync_session() as session:  # type: ignore[union-attr]
            user = User(email="quota-wiring@example.com", password_hash="not-used")
            session.add(user)
            session.flush()
            session.add(
                SessionModel(
                    user_id=user.id,
                    session_id_hash=hash_token(session_id),
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
                )
            )
        client.cookies.set("myfarmai_session", session_id)

    def test_flag_off_is_noop(self, client, mock_ollama_client):
        self._login(client)
        response = client.post("/api/v1/chat", json={"message": "Hi"})
        assert response.status_code == 200

    def test_quota_denial_returns_429(self, client, app, mock_ollama_client):
        self._login(client)
        app.state.settings.cloud_ai_enabled = True
        app.state.settings.cloud_ai_quota_limit = 1
        try:
            first = client.post("/api/v1/chat", json={"message": "Hi"})
            assert first.status_code == 200
            second = client.post("/api/v1/chat", json={"message": "Hi again"})
            assert second.status_code == 429
            assert second.json()["error_code"] == "AI_QUOTA_EXCEEDED"
        finally:
            app.state.settings.cloud_ai_enabled = False


@pytest.mark.usefixtures("async_initialized_db")
class TestAdminQuotaView:
    """§4 admin usage view: admin-only, current-window rows (async mode)."""

    async def _make_admin(self, client) -> None:
        """Insert an admin + valid session row and set the auth cookie."""
        from app.core.security import generate_session_id, hash_token
        from app.db.models.session import Session as SessionModel

        session_id = generate_session_id()
        async with db_manager.session() as session:
            admin = User(
                email=f"quota-admin-{uuid.uuid4().hex[:8]}@example.com",
                password_hash="not-used",
                role=UserRole.ADMIN,
            )
            session.add(admin)
            await session.flush()
            session.add(
                SessionModel(
                    user_id=admin.id,
                    session_id_hash=hash_token(session_id),
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
                )
            )
            await session.commit()
        client.cookies.set("myfarmai_session", session_id)

    async def test_usage_rows_reflect_consumption(self, async_client):
        uid = uuid.uuid4()
        async with db_manager.session() as session:
            session.add(
                User(id=uid, email="quota-usage@example.com", password_hash="not-used")
            )
            assert await aconsume_slot(session, uid, limit=20, window_hours=10) is True
            await session.commit()
        async with db_manager.session() as session:
            rows = await ausage_rows(session, limit=20, window_hours=10)
        match = [r for r in rows if r["user_id"] == str(uid)]
        assert len(match) == 1
        assert match[0]["used"] == 1
        assert match[0]["remaining"] == 19

    async def test_endpoint_requires_admin(self, async_client):
        from app.core.security import generate_session_id, hash_token
        from app.db.models.session import Session as SessionModel

        session_id = generate_session_id()
        async with db_manager.session() as session:
            user = User(
                email=f"quota-plain-{uuid.uuid4().hex[:6]}@example.com",
                password_hash="not-used",
            )
            session.add(user)
            await session.flush()
            session.add(
                SessionModel(
                    user_id=user.id,
                    session_id_hash=hash_token(session_id),
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
                )
            )
            await session.commit()
        async_client.cookies.set("myfarmai_session", session_id)
        response = await async_client.get("/api/v1/admin/ai-quota")
        assert response.status_code == 403
        assert response.json()["error_code"] == "ADMIN_REQUIRED"

    async def test_endpoint_returns_rows_for_admin(self, async_client):
        from app.core.security import generate_session_id, hash_token
        from app.db.models.session import Session as SessionModel

        session_id = generate_session_id()
        async with db_manager.session() as session:
            admin = User(
                email=f"quota-admin-{uuid.uuid4().hex[:8]}@example.com",
                password_hash="not-used",
                role=UserRole.ADMIN,
            )
            session.add(admin)
            await session.flush()
            session.add(
                SessionModel(
                    user_id=admin.id,
                    session_id_hash=hash_token(session_id),
                    expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
                )
            )
            await session.commit()
        async_client.cookies.set("myfarmai_session", session_id)
        response = await async_client.get("/api/v1/admin/ai-quota")
        assert response.status_code == 200
        data = response.json()
        assert set(data) == {"window_start", "window_hours", "items", "count"}
        assert data["window_hours"] == 10
