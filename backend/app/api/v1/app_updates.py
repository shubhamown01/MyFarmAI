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
_VERSION_FILE = "VERSION"
_RELEASES_URL = "https://github.com/shubhamown01/MyFarmAI/releases"
_UNKNOWN = "unknown"

# Path depth differs between the source tree (repo/backend/app/api/v1/…)
# and the container image (app/app/api/v1/…) — probe both bases.
_FILE = Path(__file__).resolve()
_CANDIDATE_BASES = (_FILE.parents[4], _FILE.parents[3], _FILE.parents[2])


def _read_version() -> str:
    import tomllib

    for base in _CANDIDATE_BASES:
        vfile = base / _VERSION_FILE
        if vfile.is_file():
            v = vfile.read_text().strip()
            if v:
                return v
        pyproject = base / "pyproject.toml"
        if pyproject.is_file():
            try:
                data = tomllib.loads(pyproject.read_text())
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
