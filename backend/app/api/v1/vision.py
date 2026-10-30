"""Crop-image assistance API (P5E): one-shot vision analysis via qwen3-vl.

Design:
- Images are processed IN MEMORY ONLY — never written to disk, never logged
  (retention requirement satisfied by construction: nothing is stored).
- Validation: magic-byte sniffing (jpeg/png/webp), 5 MiB cap, one image per
  request. Content-type headers are untrusted; bytes decide.
- No disease-detection accuracy is claimed: the system prompt yields
  observations + uncertainty + expert referral only.
- Model: qwen3-vl:2b (enabled in the registry — Model 3 gate resolved
  2026-10-31). Explicit per-request selection keeps the Phase 4 registry check
  active.
"""

import base64

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.services.ollama import OllamaClient

router = APIRouter(tags=["Vision"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_MAGIC = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


def _sniff_format(head: bytes) -> str | None:
    for magic, fmt in _MAGIC:
        if head.startswith(magic):
            return fmt
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


@router.post("/vision/analyze")
async def analyze_image(
    file: UploadFile,
    question: str = "",
    crop: str = "",
    language: str = "en",
    settings: Settings = Depends(get_settings),
    user_id=Depends(get_current_user_id),
) -> dict:
    from app.ai.prompts import build_vision_system_prompt

    data = await file.read()
    if len(data) > _MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"detail": "image too large (max 5 MiB)", "error_code": "IMAGE_TOO_LARGE"},
        )
    fmt = _sniff_format(data[:12])
    if not fmt:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "detail": "unsupported image format (jpeg/png/webp only)",
                "error_code": "UNSUPPORTED_IMAGE_FORMAT",
            },
        )

    question = question.strip()[:500]
    crop = crop.strip()[:100]
    user_content = (f"Crop: {crop}. " if crop else "") + (
        question or "Describe what you observe in this crop photo and what I should check next."
    )

    gateway_messages = [
        {"role": "system", "content": build_vision_system_prompt(language)},
        {
            "role": "user",
            "content": user_content,
            "images": [base64.b64encode(data).decode("ascii")],
        },
    ]
    try:
        response_text = await OllamaClient().chat(gateway_messages, model=settings.vision_model)
    except Exception as e:
        from app.services.ollama import (
            OllamaConnectionError,
            OllamaModelNotFoundError,
            OllamaTimeoutError,
        )

        if isinstance(e, OllamaModelNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "vision model unavailable",
                    "error_code": "VISION_MODEL_UNAVAILABLE",
                },
            ) from e
        if isinstance(e, OllamaTimeoutError):
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={"detail": "vision analysis timed out", "error_code": "VISION_TIMEOUT"},
            ) from e
        if isinstance(e, OllamaConnectionError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"detail": "AI service unavailable", "error_code": "AI_UNAVAILABLE"},
            ) from e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"detail": "vision analysis failed", "error_code": "VISION_FAILED"},
        ) from e

    return {"response": response_text, "model": settings.vision_model, "language": language}
