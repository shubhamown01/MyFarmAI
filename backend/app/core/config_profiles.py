"""Configuration profiles for different environments."""

from enum import Enum
from typing import Any


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


# Profile-specific defaults
PROFILE_DEFAULTS = {
    Environment.DEVELOPMENT: {
        "environment": "development",
        "log_level": "DEBUG",
        "ollama_base_url": "http://localhost:11434",
        "database_path": "data/app.db",
        "cors_allowed_origins": "http://localhost:3000,http://localhost:8081,http://127.0.0.1:3000",
        "rate_limit_requests": 120,
        "rate_limit_window_seconds": 60,
    },
    Environment.TEST: {
        "environment": "test",
        "log_level": "WARNING",
        "ollama_base_url": "http://localhost:11434",
        "database_path": ":memory:",
        "cors_allowed_origins": "http://testserver",
        "rate_limit_requests": 1000,
        "rate_limit_window_seconds": 60,
        "ollama_timeout_seconds": 5,
        "weather_timeout_seconds": 5,
    },
    Environment.PRODUCTION: {
        "environment": "production",
        "log_level": "INFO",
        "ollama_base_url": "http://host.docker.internal:11434",
        "database_path": "/app/data/app.db",
        "cors_allowed_origins": "",  # Must be explicitly set
        "rate_limit_requests": 60,
        "rate_limit_window_seconds": 60,
    },
}


def get_profile_defaults(env: Environment) -> dict[str, Any]:
    """Get default values for a specific environment profile."""
    return PROFILE_DEFAULTS.get(env, PROFILE_DEFAULTS[Environment.DEVELOPMENT])


def validate_production_settings(settings_dict: dict[str, Any]) -> list[str]:
    """Validate production settings and return list of errors."""
    errors = []

    if settings_dict.get("environment") == "production":
        cors = settings_dict.get("cors_allowed_origins", "")
        if not cors or cors.strip() == "":
            errors.append("CORS allowed origins must be explicitly set in production")

        if settings_dict.get("database_path", "").startswith("data/"):
            errors.append("Production database path should be absolute (e.g., /app/data/app.db)")

        if settings_dict.get("ollama_base_url", "").startswith("http://localhost"):
            errors.append("Production Ollama URL should not use localhost")

        allowed_hosts = str(settings_dict.get("allowed_hosts", "")).strip()
        if allowed_hosts in ("", "localhost,127.0.0.1", "127.0.0.1,localhost", "localhost"):
            errors.append(
                "allowed_hosts must list the real production hostname "
                "(default localhost-only would reject all real traffic)"
            )

    return errors
