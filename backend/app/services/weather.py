from typing import Any

import httpx

from app.core.config import settings

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherClient:
    def __init__(self) -> None:
        self.base_url = settings.weather_base_url.rstrip("/")
        self.timeout = settings.weather_timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_daily: bool = True,
    ) -> dict[str, Any]:
        client = await self._get_client()
        params: dict[str, str | float | int | bool] = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
        }
        if include_current:
            params["current_weather"] = "true"
        if include_daily:
            params["daily"] = (
                "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode"
            )
            params["forecast_days"] = "7"

        try:
            response = await client.get("", params=params)
            response.raise_for_status()
            data = response.json()
            return self._transform_response(data)
        except httpx.TimeoutException as e:
            raise WeatherTimeoutError(f"Weather request timed out after {self.timeout}s") from e
        except httpx.ConnectError as e:
            raise WeatherConnectionError(
                f"Cannot connect to weather service at {self.base_url}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise WeatherError(f"Weather API error: {e.response.status_code}") from e
        except Exception as e:
            raise WeatherError(f"Unexpected error calling weather service: {e}") from e

    def _transform_response(self, data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, object] = {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "generationtime_ms": data.get("generationtime_ms"),
            "utc_offset_seconds": data.get("utc_offset_seconds"),
            "timezone": data.get("timezone"),
            "timezone_abbreviation": data.get("timezone_abbreviation"),
            "elevation": data.get("elevation"),
        }

        if "current_weather" in data:
            cw = data["current_weather"]
            result["current_weather"] = {
                "temperature": cw.get("temperature"),
                "windspeed": cw.get("windspeed"),
                "winddirection": cw.get("winddirection"),
                "weathercode": cw.get("weathercode"),
                "weather_description": WEATHER_CODES.get(cw.get("weathercode"), "Unknown"),
                "time": cw.get("time"),
            }

        if "daily" in data:
            daily = data["daily"]
            daily_list: list[dict[str, object]] = []
            for i in range(len(daily.get("time", []))):
                daily_list.append(
                    {
                        "date": daily["time"][i],
                        "temperature_2m_max": daily["temperature_2m_max"][i],
                        "temperature_2m_min": daily["temperature_2m_min"][i],
                        "precipitation_sum": daily["precipitation_sum"][i],
                        "precipitation_probability_max": daily["precipitation_probability_max"][i],
                        "weathercode": daily["weathercode"][i],
                        "weather_description": WEATHER_CODES.get(
                            daily["weathercode"][i], "Unknown"
                        ),
                    }
                )
            result["daily"] = daily_list

        return result

    async def health_check(self) -> bool:
        client = await self._get_client()
        try:
            response = await client.get("", params={"latitude": 0, "longitude": 0}, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class WeatherError(Exception):
    pass


class WeatherTimeoutError(WeatherError):
    pass


class WeatherConnectionError(WeatherError):
    pass


weather_client = WeatherClient()
