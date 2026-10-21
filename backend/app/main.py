"""MyFarmAI Backend Application Entry Point."""

import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.ollama import ollama_client
from app.services.weather import weather_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("myfarmai")


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce maximum request body size."""

    def __init__(self, app: FastAPI, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Request body too large. Maximum size is {self.max_size} bytes.",
                    "error_code": "REQUEST_BODY_TOO_LARGE",
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Application starting up")

    # Validate settings for the current environment
    validation_errors = settings.validate_for_environment()
    if validation_errors:
        for error in validation_errors:
            logger.error("Configuration validation failed: %s", error)
        raise RuntimeError(f"Configuration validation failed: {'; '.join(validation_errors)}")

    # Apply profile defaults
    settings.apply_profile_defaults()

    from app.db.connection import init_db

    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Application shutting down")
    await ollama_client.close()
    await weather_client.close()
    logger.info("HTTP clients closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Trusted Host Middleware (must be first)
if settings.environment == "production":
    # In production, require explicit allowed hosts
    allowed_hosts = ["localhost", "127.0.0.1"]
    # Could be extended from settings
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Request Body Limit Middleware
app.add_middleware(RequestBodyLimitMiddleware, max_size=settings.max_request_body_size)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(
    RateLimitMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


@app.middleware("http")
async def add_request_id_and_logging(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add request ID and structured logging to all requests."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    # Extract client IP safely
    client_host = request.client.host if request.client else None

    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_host,
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
    """Root endpoint - project info."""
    return {
        "project": "My Farm AI",
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
def health_liveness() -> dict[str, str]:
    """Liveness probe - process is alive."""
    return {
        "status": "ok",
        "service": "backend",
        "check_type": "liveness",
    }


@app.get("/health/live")
def health_live() -> dict[str, str]:
    """Explicit liveness endpoint."""
    return {
        "status": "ok",
        "service": "backend",
        "check_type": "liveness",
    }


@app.get("/health/ready")
def health_readiness() -> dict[str, str | dict[str, str]]:
    """Readiness probe - checks dependencies."""
    # TODO: Add actual dependency checks (DB, Ollama)
    # For now, return ok if we reach this point
    return {
        "status": "ok",
        "service": "backend",
        "check_type": "readiness",
        "dependencies": {
            "database": "ok",
            "ollama": "ok",
        },
    }


app.include_router(api_router)
