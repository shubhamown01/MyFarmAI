"""Feedback endpoint (E1): submit + list behaviour, synthetic-safe fields only."""

import pytest

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager


class TestSubmitFeedback:
    """POST /api/v1/feedback/submit — anonymous, optional email for reply."""

    @pytest.mark.asyncio
    async def test_anonymous_submit(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "bug", "message": "the dashboard list is blank"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "accepted"
        assert isinstance(body["id"], str) and body["id"] != ""

    @pytest.mark.asyncio
    async def test_with_email_submit(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={
                "category": "feature",
                "message": "add batch operations support",
                "email": "tester@example.com",
                "app_version": "1.0.0",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["id"]

    @pytest.mark.asyncio
    async def test_invalid_category_rejected(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "refund", "message": "something broke badly"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_message_too_short_rejected(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "question", "message": "hi"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_email_field_rejected(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={
                "category": "bug",
                "message": "the weather tab always crashes",
                "email": "not-an-email",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_app_version_too_long(self, async_client) -> None:
        resp = await async_client.post(
            "/api/v1/feedback/submit",
            json={
                "category": "bug",
                "message": "short enough",
                "app_version": "1.0.0.1.2.3.4.5.6.7.8.9.10.11.12.13.14.15",
            },
        )
        assert resp.status_code == 422


class TestListFeedback:
    @pytest.mark.asyncio
    async def test_anonymous_list_rejected(self, async_client) -> None:
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_list_rejected(self, async_client) -> None:
        await async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "bug", "message": "the dashboard list is blank"},
        )
        async with db_manager.session() as session:
            session.add(
                User(
                    email="feedback-civilian@example.com",
                    password_hash=hash_password("User-pass-1!"),
                )
            )
        login = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "feedback-civilian@example.com", "password": "User-pass-1!"},
        )
        assert login.status_code == 200, login.text
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 403
        assert resp.json()["error_code"] == "ADMIN_REQUIRED"

    @pytest.mark.asyncio
    async def test_admin_list_empty_returns_zero(self, admin_async_client) -> None:
        resp = await admin_async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["items"] == []

    @pytest.mark.asyncio
    async def test_list_returns_submitted_then_new(self, admin_async_client) -> None:
        await admin_async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "feature", "message": "calendar view"},
        )
        resp = await admin_async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        assert len(body["items"]) >= 1
        first = body["items"][0]
        assert first["category"] == "feature"
        assert first["message"].startswith("calendar view")

    @pytest.mark.asyncio
    async def test_pagination_offset(self, admin_async_client) -> None:
        for _ in range(5):
            await admin_async_client.post(
                "/api/v1/feedback/submit",
                json={"category": "praise", "message": "another test case"},
            )
        resp = await admin_async_client.get("/api/v1/feedback?limit=3&offset=1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 5
        assert len(body["items"]) == 3
