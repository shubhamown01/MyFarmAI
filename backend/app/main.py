import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.config_validation import validate_settings_or_exit
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.ollama import ollama_client
from app.services.weather import weather_client

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("myfarmai")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application starting up")
    validate_settings_or_exit()
    from app.db.connection import init_db

    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Application shutting down")
    await ollama_client.close()
    await weather_client.close()
    logger.info("HTTP clients closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


@app.middleware("http")
async def add_request_id_and_logging(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
            },
        )
        return response
    except Exception as e:
        logger.exception(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e),
            },
        )
        raise


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "My Farm AI",
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "backend",
    }


app.include_router(api_router)
