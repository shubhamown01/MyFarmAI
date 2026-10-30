"""Application configuration with environment profiles."""

from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config_profiles import Environment, get_profile_defaults, validate_production_settings


class Settings(BaseSettings):
    """Application settings with environment-aware defaults."""

    # Core
    app_name: str = "My Farm AI Backend"
    app_version: str = "0.1.0"
    environment: str = Field(
        default="development", description="Environment: development, test, production"
    )

    # Ollama / LLM
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama API",
    )
    ollama_model: str = Field(
        default="qwen3:0.6b",
        description="Model name for chat completions",
    )
    ollama_timeout_seconds: int = Field(
        default=120,
        description="Request timeout for Ollama API calls",
        ge=1,
        le=300,
    )

    # Database
    database_path: str = Field(
        default="data/app.db",
        description="SQLite database file path or full SQLAlchemy URL (postgresql://...)",
    )
    database_password_file: str | None = Field(
        default=None,
        description="File containing the database password; injected into database_path "
        "when the URL lacks one (Docker secrets cannot be interpolated into env vars)",
    )

    # CORS
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8081",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR",
    )

    # Voice Service (deferred from MVP)
    voice_service_url: str = Field(
        default="http://voice:8001",
        description="Voice service URL for proxying requests",
    )

    # Weather
    weather_base_url: str = Field(
        default="https://api.open-meteo.com/v1/forecast",
        description="Open-Meteo API base URL",
    )
    weather_timeout_seconds: int = Field(
        default=10,
        description="Request timeout for weather API calls",
        ge=1,
        le=60,
    )
    weather_cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL for weather responses in seconds",
        ge=0,
    )

    # Agricultural Resources
    resources_cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL for agricultural resources in seconds",
        ge=0,
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=60,
        description="Maximum requests per window per client",
        ge=1,
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window in seconds",
        ge=1,
    )
    ai_max_concurrent_requests: int = Field(
        default=2,
        description="Maximum in-flight AI (Ollama) requests; bounds GPU/RAM pressure",
        ge=1,
    )
    ai_max_queue_depth: int = Field(
        default=10,
        description="Maximum requests waiting for an AI slot; excess rejected with 503 AI_BUSY",
        ge=0,
    )

    # Trusted proxy for rate limiting (comma-separated CIDR ranges)
    trusted_proxy_cidrs: str = Field(
        default="",
        description="Comma-separated list of trusted proxy CIDR ranges for X-Forwarded-For",
    )
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed Host headers (TrustedHostMiddleware); must list the real hostname in production",
    )

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    # Session/token lifetimes (ADR-008)
    session_ttl_hours: int = Field(
        default=24,
        description="Absolute web session lifetime in hours",
        ge=1,
    )
    session_idle_minutes: int = Field(
        default=120,
        description="Web session idle timeout in minutes",
        ge=5,
    )
    refresh_token_ttl_days: int = Field(
        default=30,
        description="Android refresh token lifetime in days",
        ge=1,
    )
    access_token_ttl_minutes: int = Field(
        default=15,
        description="Android access token lifetime in minutes",
        ge=5,
    )

    @property
    def trusted_proxy_cidrs_list(self) -> list[str]:
        return [cidr.strip() for cidr in self.trusted_proxy_cidrs.split(",") if cidr.strip()]

    # Request body limit (bytes)
    max_request_body_size: int = Field(
        default=1_048_576,  # 1 MB
        description="Maximum request body size in bytes",
        ge=1024,
    )

    # Database pool settings (PostgreSQL)
    db_pool_size: int = Field(
        default=5,
        description="Database connection pool size",
        ge=1,
        le=20,
    )
    db_max_overflow: int = Field(
        default=10,
        description="Database connection pool max overflow",
        ge=0,
        le=50,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate and normalize environment value."""
        valid = [e.value for e in Environment]
        v_lower = v.lower().strip()
        if v_lower not in valid:
            raise ValueError(f"environment must be one of {valid}, got '{v}'")
        return v_lower

    @model_validator(mode="after")
    def normalize_database_url(self) -> "Settings":
        """Inject the DB password from a file and normalize the URL driver.

        Docker secrets cannot be interpolated into environment variables, so the
        Compose backend points at postgres without a password in the URL and
        provides the secret file instead. Additionally, a bare ``postgresql://``
        URL defaults SQLAlchemy to the psycopg2 driver, which is not installed;
        the app and Alembic both use async engines, so the URL is rewritten to
        the ``postgresql+asyncpg`` dialect. SQLite paths and URLs that already
        carry a driver are left untouched.
        """
        if self.database_password_file:
            parts = urlsplit(self.database_path)
            if parts.scheme == "postgresql" and parts.password is None:
                password = Path(self.database_password_file).read_text(encoding="utf-8").strip()
                if not password:
                    raise ValueError(
                        f"database password file is empty: {self.database_password_file}"
                    )
                port = f":{parts.port}" if parts.port else ""
                netloc = f"{parts.username}:{quote(password)}@{parts.hostname}{port}"
                object.__setattr__(
                    self,
                    "database_path",
                    urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment)),
                )
        if urlsplit(self.database_path).scheme == "postgresql":
            object.__setattr__(
                self,
                "database_path",
                self.database_path.replace("postgresql://", "postgresql+asyncpg://", 1),
            )
        return self

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper().strip()
        if v_upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return v_upper

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v.strip():
            return v
        origins = [o.strip() for o in v.split(",") if o.strip()]
        for origin in origins:
            if not (origin.startswith("http://") or origin.startswith("https://")):
                raise ValueError(f"CORS origin must be a valid HTTP/HTTPS URL: {origin}")
        return v

    def apply_profile_defaults(self) -> None:
        """Apply environment-specific profile defaults for unset values."""
        env = Environment(self.environment)
        defaults = get_profile_defaults(env)
        for key, default_value in defaults.items():
            current = getattr(self, key, None)
            # Only apply if current value matches the class default (i.e., not explicitly set via env)
            # This is a heuristic; explicit env vars take precedence
            if current in (None, "", self.__class__.model_fields[key].default):
                object.__setattr__(self, key, default_value)

    def validate_for_environment(self) -> list[str]:
        """Validate settings for the current environment."""
        errors = []

        # Production-specific validations
        if self.environment == Environment.PRODUCTION:
            prod_errors = validate_production_settings(self.model_dump())
            errors.extend(prod_errors)

            # Check CORS
            if not self.cors_allowed_origins.strip():
                errors.append(
                    "CORS allowed origins must be explicitly set in production (cors_allowed_origins)"
                )

            # Check trusted proxies
            if not self.trusted_proxy_cidrs_list:
                errors.append(
                    "Trusted proxy CIDRs must be configured in production (trusted_proxy_cidrs)"
                )

            # Check request body limit is reasonable
            if self.max_request_body_size > 10_485_760:  # 10 MB
                errors.append(
                    "max_request_body_size should not exceed 10 MB in production without justification"
                )

        return errors


settings = Settings()
