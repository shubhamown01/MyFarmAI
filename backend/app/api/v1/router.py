from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.resources import router as resources_router
from app.api.v1.weather import router as weather_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(weather_router)
api_router.include_router(resources_router)
