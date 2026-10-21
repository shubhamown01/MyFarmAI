from app.core.config import settings


def validate_settings() -> list[str]:
    """Validate application settings and return list of warnings/errors."""
    issues = []

    # Validate Ollama URL format
    if not settings.ollama_base_url.startswith(("http://", "https://")):
        issues.append(
            f"OLLAMA_BASE_URL must start with http:// or https://, got: {settings.ollama_base_url}"
        )

    # Validate Ollama timeout
    if settings.ollama_timeout_seconds <= 0:
        issues.append(
            f"OLLAMA_TIMEOUT_SECONDS must be positive, got: {settings.ollama_timeout_seconds}"
        )
    elif settings.ollama_timeout_seconds > 300:
        issues.append(
            f"OLLAMA_TIMEOUT_SECONDS is very high ({settings.ollama_timeout_seconds}s), consider reducing"
        )

    # Validate weather timeout
    if settings.weather_timeout_seconds <= 0:
        issues.append(
            f"WEATHER_TIMEOUT_SECONDS must be positive, got: {settings.weather_timeout_seconds}"
        )
    elif settings.weather_timeout_seconds > 30:
        issues.append(f"WEATHER_TIMEOUT_SECONDS is high ({settings.weather_timeout_seconds}s)")

    # Validate CORS origins
    for origin in settings.cors_allowed_origins_list:
        if not origin.startswith(("http://", "https://")):
            issues.append(f"CORS origin must start with http:// or https://: {origin}")

    # Validate rate limit settings
    if settings.rate_limit_requests <= 0:
        issues.append(f"RATE_LIMIT_REQUESTS must be positive, got: {settings.rate_limit_requests}")
    if settings.rate_limit_window_seconds <= 0:
        issues.append(
            f"RATE_LIMIT_WINDOW_SECONDS must be positive, got: {settings.rate_limit_window_seconds}"
        )

    # Validate database path
    if not settings.database_path:
        issues.append("DATABASE_PATH cannot be empty")

    # Check for production-specific warnings
    if settings.environment == "production":
        if settings.cors_allowed_origins == "*" or "*" in settings.cors_allowed_origins_list:
            issues.append("CORS wildcard (*) not recommended for production")
        if settings.log_level.upper() == "DEBUG":
            issues.append("DEBUG log level not recommended for production")

    return issues


def validate_settings_or_exit() -> None:
    """Validate settings and log issues. Exit on critical errors."""
    import sys

    issues = validate_settings()
    if issues:
        import logging

        logger = logging.getLogger("myfarmai.config")
        for issue in issues:
            if "must be" in issue.lower() or "cannot be" in issue.lower():
                logger.critical("Config validation failed: %s", issue)
                sys.exit(1)
            else:
                logger.warning("Config validation warning: %s", issue)
