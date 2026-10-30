import pytest
from httpx import AsyncClient


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
