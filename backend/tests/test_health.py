import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["project"] == "My Farm AI"
        assert data["status"] == "running"
        assert data["version"] != "0.1.0"

    def test_app_version_matches_package_metadata(self):
        from importlib.metadata import version

        from app.core.config import settings

        assert settings.app_version == version("myfarmai-backend")

    @pytest.mark.asyncio
    async def test_root_health_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend"

    @pytest.mark.asyncio
    async def test_api_v1_health_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend"

    @pytest.mark.asyncio
    async def test_readiness_ok_with_ollama_disabled(self, async_client: AsyncClient, monkeypatch):
        """OLLAMA_BASE_URL="" disables the Ollama readiness check (cloud staging)."""
        from app.factory import default_settings

        monkeypatch.setattr(default_settings, "ollama_base_url", "")
        response = await async_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["dependencies"]["database"] == "ok"
        assert data["dependencies"]["ollama"] == "disabled"
