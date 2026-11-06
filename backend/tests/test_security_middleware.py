"""P3-10/P3-11 middleware tests: XFF spoofing, auth rate limits, CSRF/Origin.

Runs on the async fixture chain (aiosqlite) — auth endpoints require
db_manager async sessions.
"""

from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.session import close_db_manager, db_manager, init_db_manager
from app.factory import create_app
from app.services import auth as auth_svc


def _settings(temp_db_path: str, **overrides) -> Settings:
    defaults: dict = {
        "environment": "test",
        "database_path": f"sqlite+aiosqlite:///{temp_db_path}",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "test-model",
        "log_level": "WARNING",
    }
    defaults.update(overrides)
    return Settings(**defaults)


async def _make_app(s: Settings):
    init_db_manager(s.database_path, async_mode=True)

    from app.db.models.base import Base

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return create_app(s, test_mode=True)


async def _teardown_app() -> None:
    await close_db_manager()
    auth_svc._FAILED_LOGINS.clear()


async def _insert_session(email: str) -> str:
    """Direct row insert; returns the raw session id."""
    from app.core.security import generate_session_id, hash_token
    from app.db.models.session import Session as SessionModel
    from app.db.models.user import User

    session_id = generate_session_id()
    async with db_manager.session() as session:
        user = User(email=email, password_hash="x")
        session.add(user)
        await session.flush()
        session.add(
            SessionModel(
                user_id=user.id,
                session_id_hash=hash_token(session_id),
                expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
            )
        )
    return session_id


class TestXffSpoofing:
    async def test_spoofed_xff_ignored_for_untrusted_peer(self, temp_db_path):
        s = _settings(temp_db_path, rate_limit_requests=2, rate_limit_window_seconds=60)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                for ip in ("1.2.3.4", "5.6.7.8"):
                    resp = await c.get("/api/v1/auth/me", headers={"X-Forwarded-For": ip})
                    assert resp.status_code == 401
                # Spoofed XFF must not buy a fresh bucket.
                resp = await c.get("/api/v1/auth/me", headers={"X-Forwarded-For": "9.9.9.9"})
                assert resp.status_code == 429
                assert resp.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
        finally:
            await _teardown_app()

    async def test_xff_honored_from_trusted_proxy(self, temp_db_path):
        s = _settings(temp_db_path, rate_limit_requests=2, rate_limit_window_seconds=60)
        s.trusted_proxy_cidrs = "127.0.0.1/32"
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                for ip in ("1.2.3.4", "5.6.7.8", "9.9.9.9"):
                    resp = await c.get("/api/v1/auth/me", headers={"X-Forwarded-For": ip})
                    # Each hop gets its own bucket — never a 429.
                    assert resp.status_code == 401, resp.text
        finally:
            await _teardown_app()


class TestAuthPathLimits:
    async def test_stricter_auth_limit(self, temp_db_path):
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                for i in range(10):
                    resp = await c.post(
                        "/api/v1/auth/login",
                        json={"email": f"ghost{i}@example.com", "password": "wrong-pass-1"},
                    )
                    assert resp.status_code == 401, (i, resp.text)
                # 11th auth request from the same peer → auth limiter 429.
                resp = await c.post(
                    "/api/v1/auth/login",
                    json={"email": "ghost10@example.com", "password": "wrong-pass-1"},
                )
                assert resp.status_code == 429
                assert resp.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
        finally:
            await _teardown_app()

    async def test_account_lockout_after_five_failures(self, temp_db_path):
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                for i in range(5):
                    resp = await c.post(
                        "/api/v1/auth/login",
                        json={"email": "lock@example.com", "password": "wrong-pass-1"},
                    )
                    assert resp.status_code == 401, (i, resp.text)
                resp = await c.post(
                    "/api/v1/auth/login",
                    json={"email": "lock@example.com", "password": "wrong-pass-1"},
                )
                assert resp.status_code == 429
                assert resp.json()["error_code"] == "ACCOUNT_LOCKED"
        finally:
            await _teardown_app()


class TestCsrfOrigin:
    async def test_origin_mismatch_rejected_for_cookie_requests(self, temp_db_path):
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            session_id = await _insert_session("csrf@example.com")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                c.cookies.set("myfarmai_session", session_id)
                resp = await c.post(
                    "/api/v1/auth/logout", headers={"Origin": "https://evil.example"}
                )
                assert resp.status_code == 403
                assert resp.json()["error_code"] == "CSRF_ORIGIN_REJECTED"

                # Allowed origin passes; absent Origin (same-origin/native) passes.
                resp_ok = await c.post(
                    "/api/v1/auth/logout", headers={"Origin": "http://localhost:3000"}
                )
                assert resp_ok.status_code == 204
                resp_no_origin = await c.post("/api/v1/auth/logout")
                assert resp_no_origin.status_code == 204
        finally:
            await _teardown_app()

    async def test_cookieless_requests_unaffected(self, temp_db_path):
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/api/v1/auth/login",
                    json={"email": "a@example.com", "password": "wrong-pass-1"},
                    headers={"Origin": "https://evil.example"},
                )
                # No cookie on the request → CSRF check skipped → normal 401 flow.
                assert resp.status_code == 401
        finally:
            await _teardown_app()


class TestBodyLimits:
    async def test_chunked_body_within_limit_passes(self, temp_db_path):
        """Chunked bodies (e.g. AppSail edge proxy rewrites POSTs to chunked)
        are stream-enforced against the cap, not blanket-rejected."""
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/api/v1/chat",
                    content=b'{"message": "hi"}',
                    headers={
                        "Content-Type": "application/json",
                        "Transfer-Encoding": "chunked",
                    },
                )
                # Body passed the limit middleware and reached the route:
                # valid JSON parses, then the auth gate runs.
                assert resp.status_code == 401
                assert resp.json()["error_code"] == "NOT_AUTHENTICATED"
        finally:
            await _teardown_app()

    async def test_chunked_body_over_limit_rejected(self, temp_db_path):
        """Chunked bodies cannot bypass the size cap (security review 2026-10-29)."""
        s = _settings(temp_db_path)
        app = await _make_app(s)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                resp = await c.post(
                    "/api/v1/chat",
                    content=b"x" * (s.max_request_body_size + 1),
                    headers={"Transfer-Encoding": "chunked"},
                )
                assert resp.status_code == 413
                assert resp.json()["error_code"] == "REQUEST_BODY_TOO_LARGE"
        finally:
            await _teardown_app()
