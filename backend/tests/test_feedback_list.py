"""GET /api/v1/feedback — read-only list; anonymous; admin-gated by intent."""

import pytest


class TestListFeedback:
    @pytest.mark.asyncio
    async def test_list_empty_returns_zero(self, async_client) -> None:
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["items"] == []

    @pytest.mark.asyncio
    async def test_list_returns_submitted_then_new(self, async_client) -> None:
        await async_client.post(
            "/api/v1/feedback/submit",
            json={"category": "feature", "message": "calendar view"},
        )
        resp = await async_client.get("/api/v1/feedback?limit=10&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        assert len(body["items"]) >= 1
        first = body["items"][0]
        assert first["category"] == "feature"
        assert first["message"].startswith("calendar view")

    @pytest.mark.asyncio
    async def test_pagination_offset(self, async_client) -> None:
        for i in range(5):
            await async_client.post(
                "/api/v1/feedback/submit",
                json={"category": "praise", "message": "another test case"},
            )
        resp = await async_client.get("/api/v1/feedback?limit=3&offset=1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 5
        assert len(body["items"]) == 3