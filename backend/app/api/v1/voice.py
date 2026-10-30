"""Voice capabilities endpoint (P5F / ADR-016): clients query what voice
support exists instead of hard-coding assumptions. Server-side STT/TTS is
deferred (ADR-016 PROPOSED) — no audio ever reaches the backend."""

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings

router = APIRouter(tags=["Voice"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


@router.get("/voice/capabilities")
async def voice_capabilities(
    settings: Settings = Depends(get_settings),
    user_id=Depends(get_current_user_id),
) -> dict:
    """Voice capability discovery (ADR-016): MVP voice is client-platform
    (Android SpeechRecognizer/TTS, Web Speech API); the backend has no
    server-side STT/TTS."""
    return {
        "server_stt": False,
        "server_tts": False,
        "client_platform_voice": True,
        "recommended_languages": ["en", "hi"],
        "note": (
            "MVP voice uses client-platform speech APIs (ADR-016). Send "
            "recognized text as an ordinary chat message; no audio is "
            "accepted or stored server-side."
        ),
        "environment": settings.environment,
    }
