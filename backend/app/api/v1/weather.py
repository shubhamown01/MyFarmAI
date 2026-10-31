from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.auth import get_current_user_id
from app.schemas.weather import WeatherErrorResponse, WeatherResponse
from app.services.weather import (
    WeatherConnectionError,
    WeatherTimeoutError,
    weather_client,
)

router = APIRouter(tags=["Weather"])


@router.get(
    "/weather",
    response_model=WeatherResponse,
    responses={
        400: {"model": WeatherErrorResponse, "description": "Invalid coordinates"},
        503: {"model": WeatherErrorResponse, "description": "Weather service unavailable"},
        504: {"model": WeatherErrorResponse, "description": "Weather service timeout"},
    },
)
async def get_weather(
    user_id=Depends(get_current_user_id),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    current: bool = Query(True, description="Include current weather"),
    daily: bool = Query(True, description="Include 7-day daily forecast"),
) -> WeatherResponse:
    try:
        data = await weather_client.get_weather(
            latitude=latitude,
            longitude=longitude,
            include_current=current,
            include_daily=daily,
        )
        return WeatherResponse(**data)
    except WeatherTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"detail": str(e), "error_code": "WEATHER_TIMEOUT"},
        ) from e
    except WeatherConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Cannot connect to weather service. Please try again later.",
                "error_code": "WEATHER_CONNECTION_FAILED",
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
        ) from e


@router.get(
    "/weather/current",
    response_model=WeatherResponse,
    responses={
        400: {"model": WeatherErrorResponse, "description": "Invalid coordinates"},
        503: {"model": WeatherErrorResponse, "description": "Weather service unavailable"},
        504: {"model": WeatherErrorResponse, "description": "Weather service timeout"},
    },
)
async def get_current_weather(
    user_id=Depends(get_current_user_id),
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
) -> WeatherResponse:
    try:
        data = await weather_client.get_weather(
            latitude=latitude,
            longitude=longitude,
            include_current=True,
            include_daily=False,
        )
        return WeatherResponse(**data)
    except WeatherTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"detail": str(e), "error_code": "WEATHER_TIMEOUT"},
        ) from e
    except WeatherConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Cannot connect to weather service. Please try again later.",
                "error_code": "WEATHER_CONNECTION_FAILED",
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
        ) from e
