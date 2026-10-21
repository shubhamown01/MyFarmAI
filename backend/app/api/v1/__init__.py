from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.resources import router as resources_router
from app.api.v1.weather import router as weather_router

__all__ = ["chat_router", "health_router", "weather_router", "resources_router"]
