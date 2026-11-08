"""Public artifact downloads (B-3): the Android APK for external testers.

Disabled until ``settings.public_dir`` points at a build-time-injected
directory (default empty). Serving is intentionally unauthenticated — it
publishes the test APK, never user data — and stays behind the app-wide
rate limiter. Guarded to APK-named files only.
"""

from mimetypes import guess_type
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.v1.chat import get_settings
from app.core.config import Settings

router = APIRouter(tags=["Downloads"])

_ALLOWED = {"app-release.apk"}
_NOT_FOUND = HTTPException(
    status_code=404,
    detail={"detail": "not found", "error_code": "NOT_FOUND"},
)


def _resolve(settings: Settings, name: str) -> Path:
    if not settings.public_dir or name not in _ALLOWED:
        raise _NOT_FOUND
    path = (Path(settings.public_dir) / name).resolve()
    if not path.is_file():
        raise _NOT_FOUND
    return path


@router.get("/downloads/{name}", include_in_schema=False)
async def download_public(
    name: str,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = _resolve(settings, name)
    media = guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(
        path,
        media_type=media,
        filename="myfarmai-app-release.apk",
        headers={"Cache-Control": "no-store"},
    )
