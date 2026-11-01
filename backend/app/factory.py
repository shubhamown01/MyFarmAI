"""Application factory for creating FastAPI instances with custom settings."""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.core.config import Settings
from app.core.config import settings as default_settings
from app.db.session import close_db_manager, db_manager, init_db_manager
from app.middleware.csrf import CSRFOriginMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.ollama import ollama_client
from app.services.weather import weather_client


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce maximum request body size."""

    def __init__(self, app: FastAPI, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        content_length = request.headers.get("content-length")
        # Exit-gate condition (security review 2026-10-29): chunked uploads
        # have no Content-Length and would bypass the limit; bodies here are
        # small JSON, so reject rather than stream-enforce.
        if request.headers.get("transfer-encoding", "").lower() == "chunked":
            return JSONResponse(
                status_code=413,
                content={
                    "detail": "Chunked request bodies are not accepted.",
                    "error_code": "REQUEST_BODY_TOO_LARGE",
                },
                headers={"Retry-After": "60"},
            )
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


def create_app(custom_settings: Settings | None = None, *, test_mode: bool = False) -> FastAPI:
    """Create a FastAPI application with the given settings.

    Args:
        custom_settings: Optional custom settings. If not provided, uses default settings.
        test_mode: If True, skips lifespan and uses test database configuration.

    Returns:
        Configured FastAPI application.
    """
    app_settings = custom_settings or default_settings

    # Configure logging. Request-ID-aware formatter: middleware passes the id
    # via extra={}, which the default formatter drops — without this, request
    # IDs never appear in log lines and incidents can't be correlated.
    class _RequestIdFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            base = super().format(record)
            rid = getattr(record, "request_id", None)
            return f"{base} request_id={rid}" if rid else base

    _handler = logging.StreamHandler()
    _handler.setFormatter(_RequestIdFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(
        level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
        handlers=[_handler],
    )
    logger = logging.getLogger("myfarmai")

    # Initialize database manager before creating the app (needed for test_mode)
    # Only initialize if not already initialized (e.g., by test fixtures)
    is_test = test_mode and app_settings.database_path.startswith("sqlite")

    if not db_manager.is_initialized:
        init_db_manager(app_settings.database_path, async_mode=not is_test)
        # Redact credentials before logging the DSN (password must never hit logs).
        _safe_dsn = urlsplit(app_settings.database_path)
        _netloc = (
            _safe_dsn.netloc.split("@", 1)[-1] if "@" in _safe_dsn.netloc else _safe_dsn.netloc
        )
        logger.info(
            "Database manager initialized with %s://%s%s (async=%s)",
            _safe_dsn.scheme,
            _netloc,
            _safe_dsn.path,
            not is_test,
        )
    else:
        logger.info("Database manager already initialized, skipping initialization")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Application starting up")

        # Validate settings for the current environment
        validation_errors = app_settings.validate_for_environment()
        if validation_errors:
            for error in validation_errors:
                logger.error("Configuration validation failed: %s", error)
            raise RuntimeError(f"Configuration validation failed: {'; '.join(validation_errors)}")

        # Apply profile defaults
        app_settings.apply_profile_defaults()

        # Run alembic migrations for PostgreSQL
        if app_settings.database_path.startswith("postgresql"):
            try:

                def _run_migrations() -> None:
                    from alembic import command
                    from alembic.config import Config

                    alembic_cfg = Config("alembic.ini")
                    # configparser treats '%' as interpolation syntax; escape it so
                    # URL-encoded characters in the password survive set_main_option.
                    alembic_cfg.set_main_option(
                        "sqlalchemy.url", app_settings.database_path.replace("%", "%%")
                    )
                    command.upgrade(alembic_cfg, "head")

                # Alembic's async env.py calls asyncio.run(), which fails inside
                # the already-running lifespan loop; execute it in a worker thread.
                await asyncio.to_thread(_run_migrations)
                logger.info("Database migrations applied successfully")
            except Exception as e:
                logger.error("Failed to apply database migrations: %s", e)
                raise RuntimeError(f"Database migration failed: {e}") from e

        yield

        logger.info("Application shutting down")
        await ollama_client.close()
        await weather_client.close()
        await close_db_manager()
        logger.info("Database connections closed")

    # Create FastAPI application
    lifespan_func = lifespan if not test_mode else None
    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan_func,
        docs_url="/docs" if app_settings.environment != "production" else None,
        redoc_url="/redoc" if app_settings.environment != "production" else None,
    )

    # Store settings in app state for dependency injection
    app.state.settings = app_settings

    # Trusted Host Middleware
    if app_settings.environment == "production":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=app_settings.allowed_hosts_list)

    # Request Body Limit Middleware
    app.add_middleware(RequestBodyLimitMiddleware, max_size=app_settings.max_request_body_size)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Rate Limiting Middleware (global, per-IP)
    app.add_middleware(
        RateLimitMiddleware,
        requests=app_settings.rate_limit_requests,
        window_seconds=app_settings.rate_limit_window_seconds,
        trusted_proxy_cidrs=app_settings.trusted_proxy_cidrs_list,
    )

    # Stricter per-IP limit for auth endpoints (brute-force mitigation, P3-11)
    app.add_middleware(
        RateLimitMiddleware,
        requests=10,
        window_seconds=60,
        trusted_proxy_cidrs=app_settings.trusted_proxy_cidrs_list,
        path_prefix="/api/v1/auth",
    )

    # CSRF/Origin enforcement for cookie-authenticated state changes (P3-10)
    from app.api.v1.auth import SESSION_COOKIE

    app.add_middleware(
        CSRFOriginMiddleware,
        allowed_origins=app_settings.cors_allowed_origins_list,
        cookie_name=SESSION_COOKIE,
    )

    @app.middleware("http")
    async def add_request_id_and_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add request ID and structured logging to all requests."""
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

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
        return {
            "project": "My Farm AI",
            "version": app_settings.app_version,
            "status": "running",
        }

    @app.get("/health")
    def health_liveness() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "backend",
            "check_type": "liveness",
        }

    @app.get("/health/live")
    def health_live() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "backend",
            "check_type": "liveness",
        }

    @app.get("/health/ready")
    async def health_readiness() -> JSONResponse:
        """Readiness probe with real dependency checks.

        Reports 503 with per-dependency status when any dependency is
        unreachable; 200 only when the database and Ollama are both reachable.
        """
        from sqlalchemy import text

        db_ok, ollama_ok = False, False
        try:
            async with db_manager.session() as session:
                await session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            logger.warning("Readiness check: database unreachable")
        try:
            ollama_ok = await ollama_client.health_check()
        except Exception:
            logger.warning("Readiness check: ollama unreachable")

        deps: dict[str, str] = {
            "database": "ok" if db_ok else "unreachable",
            "ollama": "ok" if ollama_ok else "unreachable",
        }
        status = "ok" if db_ok and ollama_ok else "degraded"
        return JSONResponse(
            status_code=200 if status == "ok" else 503,
            content={
                "status": status,
                "service": "backend",
                "check_type": "readiness",
                "dependencies": deps,
            },
        )

    app.include_router(api_router)

    @app.exception_handler(HTTPException)
    async def flatten_error_envelope(request: Request, exc: HTTPException) -> JSONResponse:
        """Uniform flat error envelope (ADR-009): {detail, error_code}.

        Exit-gate fast-follow: endpoints nest error_code inside detail;
        middlewares already emit the flat shape. Flatten both so clients
        parse one shape.
        """
        body = exc.detail
        if isinstance(body, dict) and "error_code" in body:
            return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": body, "error_code": "HTTP_ERROR"},
            headers=exc.headers,
        )

    return app


# Default app instance for backward compatibility (lazy initialization)
_default_app: FastAPI | None = None


def get_default_app() -> FastAPI:
    """Get the default app instance, creating it if necessary."""
    global _default_app
    if _default_app is None:
        _default_app = create_app(default_settings)
    return _default_app


# For backward compatibility - provide app as a callable that returns the default app
def app() -> FastAPI:
    """Get the default app instance (for backward compatibility)."""
    return get_default_app()
