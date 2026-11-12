"""Downloads route (B-3): public APK serving behaviour."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings


def _app_with_public_dir(tmp_path: Path):
    from app.factory import create_app

    settings = Settings(public_dir=str(tmp_path), environment="test")
    return create_app(custom_settings=settings)


class TestDownloads:
    @pytest.mark.asyncio
    async def test_disabled_by_default_404(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/api/v1/downloads/app-release.apk")
        assert resp.status_code == 404
        assert resp.json()["error_code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_serves_apk_when_enabled(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MYFARMAI_PUBLIC_DIR", str(tmp_path))
        apk = tmp_path / "app-release.apk"
        apk.write_bytes(b"PK\x03\x04fake")
        app = _app_with_public_dir(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.get("/api/v1/downloads/app-release.apk")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/vnd.android.package-archive")
        assert b"PK\x03\x04" in resp.content

    @pytest.mark.asyncio
    async def test_head_returns_headers_without_body(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MYFARMAI_PUBLIC_DIR", str(tmp_path))
        apk = tmp_path / "app-release.apk"
        apk.write_bytes(b"PK\x03\x04fake")
        app = _app_with_public_dir(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.head("/api/v1/downloads/app-release.apk")
        assert resp.status_code == 200
        assert resp.headers["content-length"] == str(apk.stat().st_size)
        assert resp.content == b""

    @pytest.mark.asyncio
    async def test_unknown_name_404(self, tmp_path: Path) -> None:
        app = _app_with_public_dir(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            resp = await c.get("/api/v1/downloads/secrets.env")
        assert resp.status_code == 404
