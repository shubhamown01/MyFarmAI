"""Auth API integration tests (P3-07/P3-08) — async mode (aiosqlite)."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")


async def _make_user(email: str, password: str, role: UserRole = UserRole.USER) -> User:
    """Create an account directly in the test DB."""
    async with db_manager.session() as session:
        user = User(email=email, password_hash=hash_password(password), role=role)
        session.add(user)
        return user


class TestWebCookieFlow:
    async def test_login_sets_httponly_cookie(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "User-pass-1!"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["access_token"] is None
        cookie = resp.headers.get("set-cookie", "")
        assert "myfarmai_session=" in cookie
        assert "httponly" in cookie.lower()
        assert "samesite=lax" in cookie.lower()

    async def test_me_returns_user_from_cookie(self, async_client: AsyncClient) -> None:
        user = await _make_user("user@example.com", "User-pass-1!")
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "User-pass-1!"},
        )
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "user@example.com"
        assert resp.json()["id"] == str(user.id)

    async def test_me_without_session_401(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "NOT_AUTHENTICATED"

    async def test_logout_revokes_and_clears_cookie(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "User-pass-1!"},
        )
        assert (await async_client.get("/api/v1/auth/me")).status_code == 200
        resp = await async_client.post("/api/v1/auth/logout")
        assert resp.status_code == 204
        # Regression 2026-11-08: returning a fresh Response discarded the
        # delete_cookie header, so browsers kept the session cookie.
        assert "myfarmai_session=" in resp.headers.get("set-cookie", "")
        assert (await async_client.get("/api/v1/auth/me")).status_code == 401

    async def test_bearer_token_also_accepted(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "User-pass-1!"},
        )
        session_id = resp.cookies.get("myfarmai_session")
        assert session_id
        resp2 = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_id}"},
        )
        assert resp2.status_code == 200


class TestLoginErrors:
    async def test_generic_error_no_account_disclosure(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        unknown = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "wrong-pass-1"},
        )
        wrongpw = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong-pass-1"},
        )
        assert unknown.status_code == wrongpw.status_code == 401
        assert unknown.json() == wrongpw.json()

    async def test_malformed_email_rejected(self, async_client: AsyncClient) -> None:
        resp = await async_client.post(
            "/api/v1/auth/login", json={"email": "not-an-email", "password": "whatever1"}
        )
        assert resp.status_code == 422

    async def test_short_password_rejected(self, async_client: AsyncClient) -> None:
        resp = await async_client.post(
            "/api/v1/auth/login", json={"email": "x@example.com", "password": "short"}
        )
        assert resp.status_code == 422


class TestAndroidTokenFlow:
    async def test_android_login_returns_tokens(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "User-pass-1!", "android": True},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"] and body["refresh_token"]
        # Android login must not set a web session cookie.
        assert "myfarmai_session=" not in resp.headers.get("set-cookie", "")

    async def test_refresh_rotates_and_old_token_dies(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        login = (
            await async_client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "User-pass-1!", "android": True},
            )
        ).json()
        r1 = await async_client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert r1.status_code == 200
        assert r1.json()["refresh_token"] != login["refresh_token"]
        # Old refresh is single-use.
        r2 = await async_client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": login["refresh_token"]}
        )
        assert r2.status_code == 401
        assert r2.json()["error_code"] == "REFRESH_INVALID"

    async def test_refresh_reuse_kills_new_token(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        login = (
            await async_client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "User-pass-1!", "android": True},
            )
        ).json()
        r1 = (
            await async_client.post(
                "/api/v1/auth/token/refresh", json={"refresh_token": login["refresh_token"]}
            )
        ).json()
        # Replay the rotated-out token.
        await async_client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": login["refresh_token"]}
        )
        # The token issued by that first refresh must now also be dead.
        r3 = await async_client.post(
            "/api/v1/auth/token/refresh", json={"refresh_token": r1["refresh_token"]}
        )
        assert r3.status_code == 401

    async def test_android_access_token_valid_for_me(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        login = (
            await async_client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "User-pass-1!", "android": True},
            )
        ).json()
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert resp.status_code == 200


class TestAdminAccounts:
    async def test_admin_can_create_user(self, async_client: AsyncClient) -> None:
        await _make_user("admin@example.com", "Admin-pass-1!", UserRole.ADMIN)
        await async_client.post(
            "/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin-pass-1!"}
        )
        resp = await async_client.post(
            "/api/v1/auth/admin/users",
            json={"email": "new@example.com", "password": "New-pass-1!"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["role"] == "user"

    async def test_non_admin_forbidden(self, async_client: AsyncClient) -> None:
        await _make_user("user@example.com", "User-pass-1!")
        await async_client.post(
            "/api/v1/auth/login", json={"email": "user@example.com", "password": "User-pass-1!"}
        )
        resp = await async_client.post(
            "/api/v1/auth/admin/users",
            json={"email": "new2@example.com", "password": "New-pass-1!"},
        )
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "FORBIDDEN"

    async def test_anonymous_forbidden_from_admin_endpoint(self, async_client: AsyncClient) -> None:
        resp = await async_client.post(
            "/api/v1/auth/admin/users",
            json={"email": "new3@example.com", "password": "New-pass-1!"},
        )
        assert resp.status_code == 401

    async def test_duplicate_email_conflict(self, async_client: AsyncClient) -> None:
        await _make_user("admin@example.com", "Admin-pass-1!", UserRole.ADMIN)
        await async_client.post(
            "/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin-pass-1!"}
        )
        resp = await async_client.post(
            "/api/v1/auth/admin/users",
            json={"email": "admin@example.com", "password": "New-pass-1!"},
        )
        assert resp.status_code == 409
