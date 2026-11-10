from fastapi import APIRouter

from app.api.v1.admin_quota import router as admin_quota_router
from app.api.v1.app_updates import router as app_updates_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.crop_cycles import router as crop_cycles_router
from app.api.v1.crop_plans import router as crop_plans_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.downloads import router as downloads_router
from app.api.v1.farms import router as farms_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.health import router as health_router
from app.api.v1.land import router as land_router
from app.api.v1.profile import router as profile_router
from app.api.v1.research import router as research_router
from app.api.v1.resources import router as resources_router
from app.api.v1.verification import router as verification_router
from app.api.v1.vision import router as vision_router
from app.api.v1.voice import router as voice_router
from app.api.v1.weather import router as weather_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(farms_router)
api_router.include_router(land_router)
api_router.include_router(profile_router)
api_router.include_router(research_router)
api_router.include_router(vision_router)
api_router.include_router(voice_router)
api_router.include_router(crop_cycles_router)
api_router.include_router(crop_plans_router)
api_router.include_router(dashboard_router)
api_router.include_router(conversations_router)
api_router.include_router(weather_router)
api_router.include_router(resources_router)
api_router.include_router(verification_router)
api_router.include_router(admin_quota_router)
api_router.include_router(feedback_router)
api_router.include_router(app_updates_router)
api_router.include_router(downloads_router)
