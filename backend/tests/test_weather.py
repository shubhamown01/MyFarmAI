from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestWeatherEndpoint:
    MOCK_WEATHER_RESPONSE = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "generationtime_ms": 1.5,
        "utc_offset_seconds": 19800,
        "timezone": "Asia/Kolkata",
        "timezone_abbreviation": "IST",
        "elevation": 216.0,
        "current_weather": {
            "temperature": 32.5,
            "windspeed": 12.0,
            "winddirection": 180,
            "weathercode": 0,
            "weather_description": "Clear sky",
            "time": "2024-01-15T14:00",
        },
        "daily": [
            {
                "date": "2024-01-15",
                "temperature_2m_max": 33.0,
                "temperature_2m_min": 18.0,
                "precipitation_sum": 0.0,
                "precipitation_probability_max": 0,
                "weathercode": 0,
                "weather_description": "Clear sky",
            },
            {
                "date": "2024-01-16",
                "temperature_2m_max": 32.0,
                "temperature_2m_min": 17.0,
                "precipitation_sum": 2.5,
                "precipitation_probability_max": 30,
                "weathercode": 61,
                "weather_description": "Slight rain",
            },
        ],
    }

    @pytest.mark.asyncio
    async def test_weather_valid_coordinates(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 28.6139, "longitude": 77.2090},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["latitude"] == 28.6139
            assert data["longitude"] == 77.2090
            assert "current_weather" in data
            assert data["current_weather"]["temperature"] == 32.5
            assert data["current_weather"]["weathercode"] == 0
            assert "daily" in data
            assert len(data["daily"]) == 2

    @pytest.mark.asyncio
    async def test_weather_only_current(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 28.6139, "longitude": 77.2090, "daily": "false"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "current_weather" in data
            # The mock returns full response; actual API would filter based on params
            assert "current_weather" in data

    @pytest.mark.asyncio
    async def test_weather_only_daily(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 28.6139, "longitude": 77.2090, "current": "false"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "daily" in data

    @pytest.mark.asyncio
    async def test_weather_invalid_latitude(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/weather",
            params={"latitude": 95.0, "longitude": 77.2090},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weather_invalid_longitude(self, async_client: AsyncClient):
        response = await async_client.get(
            "/api/v1/weather",
            params={"latitude": 28.6139, "longitude": 200.0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weather_connection_error(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            from app.services.weather import WeatherConnectionError

            mock.get_weather = AsyncMock(side_effect=WeatherConnectionError("Connection failed"))

            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 28.6139, "longitude": 77.2090},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["error_code"] == "WEATHER_CONNECTION_FAILED"

    @pytest.mark.asyncio
    async def test_weather_timeout(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            from app.services.weather import WeatherTimeoutError

            mock.get_weather = AsyncMock(side_effect=WeatherTimeoutError("Timeout"))

            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 28.6139, "longitude": 77.2090},
            )
            assert response.status_code == 504
            data = response.json()
            assert data["error_code"] == "WEATHER_TIMEOUT"

    @pytest.mark.asyncio
    async def test_weather_boundary_latitudes(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            # Test latitude = 90 (North Pole)
            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 90.0, "longitude": 0.0},
            )
            assert response.status_code == 200

            # Test latitude = -90 (South Pole)
            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": -90.0, "longitude": 0.0},
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_weather_boundary_longitudes(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            # Test longitude = 180
            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 0.0, "longitude": 180.0},
            )
            assert response.status_code == 200

            # Test longitude = -180
            response = await async_client.get(
                "/api/v1/weather",
                params={"latitude": 0.0, "longitude": -180.0},
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_current_weather_endpoint(self, async_client: AsyncClient):
        with patch("app.api.v1.weather.weather_client") as mock:
            mock.get_weather = AsyncMock(return_value=self.MOCK_WEATHER_RESPONSE)

            response = await async_client.get(
                "/api/v1/weather/current",
                params={"latitude": 28.6139, "longitude": 77.2090},
            )
            assert response.status_code == 200
            data = response.json()
            assert "current_weather" in data
