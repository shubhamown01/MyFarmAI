"""GET /api/v1/feedback — admin-only read of submissions (regression: was public)."""

import pytest

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager


class TestListFeedbackAuth:
    @pytest.mark.asyncio
    async def test_anonymous_denied(self, async_client) -> None:
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_denied(self, async_client) -> None:
        async with db_manager.session() as session:
            session.add(
                User(
                    email="list-civilian@example.com",
                    password_hash=hash_password("User-pass-1!"),
                )
            )
        login = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "list-civilian@example.com", "password": "User-pass-1!"},
        )
        assert login.status_code == 200, login.text
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_admin_sees_submitted_rows(self, admin_async_client) -> None:
        await admin_async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "bug", "message": "export button does nothing"},
        )
        resp = await admin_async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        assert body["items"][0]["message"].startswith("export button")
