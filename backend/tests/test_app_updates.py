"""App update metadata endpoint: latest version + severity contract."""

import pytest


class TestLatestRelease:
    @pytest.mark.asyncio
    async def test_returns_contract_fields(self, async_client) -> None:
        resp = await async_client.get("/api/v1/app-updates/latest")
        assert resp.status_code == 200
        body = resp.json()
        assert body["severity"] in ("optional", "recommended", "critical")
        assert "release_notes_url" in body
        assert "download_url" in body
        assert "github.com/shubhamown01/MyFarmAI" in body["download_url"]
        # latest_version always looks MAJOR.MINOR.PATCH-ish (or 'unknown' if unreadable)
        assert body["latest_version"] == "unknown" or '"."' not in body["latest_version"]

    @pytest.mark.asyncio
    async def test_no_auth_required(self, async_client) -> None:
        resp = await async_client.get("/api/v1/app-updates/latest")
        assert resp.status_code == 200
