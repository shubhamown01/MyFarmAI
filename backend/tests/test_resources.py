import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
async def _authed_client(async_client: AsyncClient, request):
    """6C M1: weather/resources now require auth — log in before each test."""
    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.session import db_manager

    email = f"auth-{abs(hash(request.node.nodeid)) % 10**10}@verifytest.com"
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("Pass-2026!x")))
    resp = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"}
    )
    assert resp.status_code == 200, resp.text
    return async_client


class TestResourcesEndpoint:
    @pytest.mark.asyncio
    async def test_list_all_resources(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "total" in data
        assert "categories" in data
        assert data["total"] > 0
        assert len(data["resources"]) == data["total"]
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0

    @pytest.mark.asyncio
    async def test_resource_structure(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources")
        assert response.status_code == 200
        data = response.json()
        for resource in data["resources"]:
            assert "title" in resource
            assert "category" in resource
            assert "url" in resource
            assert "source" in resource
            assert "description" in resource
            assert isinstance(resource["title"], str)
            assert isinstance(resource["category"], str)
            assert isinstance(resource["url"], str)
            assert isinstance(resource["source"], str)
            assert isinstance(resource["description"], str)
            assert resource["url"].startswith("http")

    @pytest.mark.asyncio
    async def test_filter_by_category_schemes(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/resources",
            params={"category": "schemes"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for resource in data["resources"]:
            assert resource["category"] == "schemes"

    @pytest.mark.asyncio
    async def test_filter_by_category_advisory(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/resources",
            params={"category": "advisory"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for resource in data["resources"]:
            assert resource["category"] == "advisory"

    @pytest.mark.asyncio
    async def test_filter_by_category_case_insensitive(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/resources",
            params={"category": "SCHEMES"},
        )
        assert response.status_code == 200
        data = response.json()
        for resource in data["resources"]:
            assert resource["category"].lower() == "schemes"

    @pytest.mark.asyncio
    async def test_filter_by_nonexistent_category(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/resources",
            params={"category": "nonexistent"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["resources"] == []

    @pytest.mark.asyncio
    async def test_list_categories(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "schemes" in data
        assert "advisory" in data
        assert "market" in data

    @pytest.mark.asyncio
    async def test_get_resources_by_category_path(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources/schemes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for resource in data["resources"]:
            assert resource["category"] == "schemes"

    @pytest.mark.asyncio
    async def test_get_resources_by_nonexistent_category_path(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "CATEGORY_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_known_resources_exist(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources")
        assert response.status_code == 200
        data = response.json()
        titles = [r["title"] for r in data["resources"]]
        assert "ICAR - Indian Council of Agricultural Research" in titles
        assert "PM-KISAN - Pradhan Mantri Kisan Samman Nidhi" in titles
        assert "eNAM - National Agriculture Market" in titles
        assert "IMD - India Meteorological Department" in titles

    @pytest.mark.asyncio
    async def test_sources_are_official(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources")
        assert response.status_code == 200
        data = response.json()
        sources = [r["source"] for r in data["resources"]]
        official_sources = [
            "ICAR",
            "Ministry of Agriculture & Farmers Welfare",
            "Ministry of Earth Sciences",
            "NABARD",
            "NPCI",
        ]
        for source in official_sources:
            assert source in sources

    @pytest.mark.asyncio
    async def test_categories_match_resources(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/resources")
        assert response.status_code == 200
        data = response.json()
        resource_categories = {r["category"] for r in data["resources"]}
        assert set(data["categories"]) == resource_categories


async def test_resources_requires_auth(async_client: AsyncClient):
    """6C M1: resources must require authentication."""
    async_client.cookies.clear()  # autouse fixture leaves a session cookie
    resp = await async_client.get("/api/v1/resources")
    assert resp.status_code == 401


async def test_resources_categories_and_category_require_auth(async_client: AsyncClient):
    """6C M1 (QA-caught gap): the remaining /resources endpoints need auth too."""
    async_client.cookies.clear()
    assert (await async_client.get("/api/v1/resources/categories")).status_code == 401
    assert (await async_client.get("/api/v1/resources/crops")).status_code == 401
