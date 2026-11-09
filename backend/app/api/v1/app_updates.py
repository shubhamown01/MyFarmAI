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

_VERSION_FILE = Path(__file__).resolve().parents[3] / "VERSION"
_RELEASES_URL = "https://github.com/shubhamown01/MyFarmAI/releases"


def _read_version() -> str:
    try:
        return _VERSION_FILE.read_text().strip()
    except OSError:
        return "unknown"


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
