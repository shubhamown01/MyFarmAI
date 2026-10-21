from pydantic import BaseModel, Field, field_validator


class WeatherRequest(BaseModel):
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees",
    )

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v < -90.0 or v > 90.0:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v < -180.0 or v > 180.0:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v


class CurrentWeather(BaseModel):
    temperature: float = Field(..., description="Air temperature at 2m in Celsius")
    windspeed: float = Field(..., description="Wind speed at 10m in km/h")
    winddirection: int = Field(..., description="Wind direction in degrees")
    weathercode: int = Field(..., description="WMO weather condition code")
    time: str = Field(..., description="Observation time in ISO 8601 format")


class DailyForecast(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    temperature_2m_max: float = Field(..., description="Maximum temperature in Celsius")
    temperature_2m_min: float = Field(..., description="Minimum temperature in Celsius")
    precipitation_sum: float = Field(..., description="Total precipitation in mm")
    precipitation_probability_max: int = Field(
        ..., description="Maximum precipitation probability in %"
    )
    weathercode: int = Field(..., description="WMO weather condition code")


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    current_weather: CurrentWeather | None = None
    daily: list[DailyForecast] | None = None


class WeatherErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
