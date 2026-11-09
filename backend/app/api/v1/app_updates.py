"""App update metadata endpoint (public, unauthenticated).

Serves the latest published application version + severity so the Android
app can run its update check. Reads the single VERSION file at import time;
no user data, no telemetry, no download-by-default (the client only opens
the official GitHub Releases page when the user taps it).
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/app-updates", tags=["AppUpdates"])

# VERSION file (repo root, canonical) may not be present in the container
# image; pyproject.toml always is — both are kept in sync manually.
_VERSION_FILE = Path(__file__).resolve().parents[4] / "VERSION"
_PYPROJECT = Path(__file__).resolve().parents[4] / "backend" / "pyproject.toml"
_RELEASES_URL = "https://github.com/shubhamown01/MyFarmAI/releases"
_UNKNOWN = "unknown"


def _read_version() -> str:
    if _VERSION_FILE.is_file():
        v = _VERSION_FILE.read_text().strip()
        if v:
            return v
    if _PYPROJECT.is_file():
        try:
            import tomllib

            data = tomllib.loads(_PYPROJECT.read_text())
            v = str(data.get("project", {}).get("version", "")).strip()
            if v:
                return v
        except (OSError, ValueError, KeyError):
            pass
    return _UNKNOWN


@router.get("/latest", include_in_schema=True)
async def latest_release() -> dict[str, Any]:
    """Official release metadata for the in-app update check."""
    version = _read_version()
    return {
        "latest_version": version,
        "minimum_supported_version": "0.9.0",
        "severity": "optional",
        "release_notes_url": f"{_RELEASES_URL}/tag/v{version}",
        "download_url": f"{_RELEASES_URL}/latest",
        "published_at": None,  # filled from the release record once known
    }
