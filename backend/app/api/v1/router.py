from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.crop_cycles import router as crop_cycles_router
from app.api.v1.farms import router as farms_router
from app.api.v1.health import router as health_router
from app.api.v1.research import router as research_router
from app.api.v1.resources import router as resources_router
from app.api.v1.weather import router as weather_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(farms_router)
api_router.include_router(research_router)
api_router.include_router(crop_cycles_router)
api_router.include_router(conversations_router)
api_router.include_router(weather_router)
api_router.include_router(resources_router)
