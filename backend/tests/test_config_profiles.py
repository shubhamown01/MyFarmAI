"""Production-settings validation (6C audit M2: allowed_hosts must be explicit)."""

from app.core.config_profiles import validate_production_settings


def _prod(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "environment": "production",
        "cors_allowed_origins": "https://farm.example.com",
        "database_path": "/app/data/app.db",
        "ollama_base_url": "http://ollama.internal:11434",
        "allowed_hosts": "localhost,127.0.0.1",
    }
    base.update(over)
    return base


def test_production_default_allowed_hosts_rejected() -> None:
    """6C M2: the localhost-only default must not pass production validation."""
    errors = validate_production_settings(_prod())
    assert any("allowed_hosts" in e for e in errors)


def test_production_explicit_allowed_hosts_passes() -> None:
    errors = validate_production_settings(_prod(allowed_hosts="farm.example.com"))
    assert errors == []


def test_non_production_skips_checks() -> None:
    assert validate_production_settings({"environment": "development"}) == []
