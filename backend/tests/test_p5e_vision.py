"""P5E tests: vision endpoint — byte-level validation, in-memory-only
processing, error mapping, registry-enabled model."""

import base64
import io

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")

JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


async def _login(client: AsyncClient, email: str) -> None:
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("Pass-2026!x")))
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"})
    assert resp.status_code == 200, resp.text


def _file(data: bytes, name: str = "photo.jpg", mime: str = "image/jpeg") -> dict:
    return {"file": (name, io.BytesIO(data), mime)}


async def test_analyze_requires_auth(async_client: AsyncClient) -> None:
    resp = await async_client.post("/api/v1/vision/analyze", files=_file(JPEG_BYTES))
    assert resp.status_code == 401


async def test_rejects_non_image_bytes(async_client: AsyncClient) -> None:
    await _login(async_client, "p5e-a@verifytest.com")
    resp = await async_client.post(
        "/api/v1/vision/analyze",
        files=_file(b"just text, not an image", name="evil.jpg"),
    )
    assert resp.status_code == 415
    assert resp.json()["error_code"] == "UNSUPPORTED_IMAGE_FORMAT"


async def test_rejects_oversized_image(async_client: AsyncClient) -> None:
    await _login(async_client, "p5e-b@verifytest.com")
    big = JPEG_BYTES + b"\x00" * (5 * 1024 * 1024)
    resp = await async_client.post("/api/v1/vision/analyze", files=_file(big))
    assert resp.status_code == 413


async def test_content_type_header_untrusted_bytes_decide(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, "p5e-c@verifytest.com")
    resp = await async_client.post(
        "/api/v1/vision/analyze",
        files=_file(b"not an image", name="ok.png", mime="image/png"),
    )
    assert resp.status_code == 415  # magic bytes, not the declared mime


async def test_valid_jpeg_calls_gateway_and_returns_response(
    async_client: AsyncClient, monkeypatch
) -> None:
    await _login(async_client, "p5e-d@verifytest.com")

    captured = {}

    async def fake_chat(self, messages, model=None):
        captured["messages"] = messages
        captured["model"] = model
        return "Observed: yellowing leaves. Possible: nitrogen deficiency (uncertain)."

    from app.services.ollama import OllamaClient

    monkeypatch.setattr(OllamaClient, "chat", fake_chat)
    resp = await async_client.post(
        "/api/v1/vision/analyze",
        files=_file(JPEG_BYTES),
        data={"crop": "tomato", "question": "leaves are yellow", "language": "en"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "yellowing" in body["response"]
    assert body["model"] == "qwen3-vl:2b"
    msgs = captured["messages"]
    assert msgs[0]["role"] == "system"
    assert "Never claim a definitive disease diagnosis" in msgs[0]["content"]
    assert "Never invent pesticide doses" in msgs[0]["content"]
    img = msgs[1]["images"][0]
    assert base64.b64decode(img) == JPEG_BYTES  # round-trip, in-memory only


async def test_model_not_found_maps_503(async_client: AsyncClient, monkeypatch) -> None:
    from app.services.ollama import OllamaClient, OllamaModelNotFoundError

    await _login(async_client, "p5e-e@verifytest.com")

    async def fail(self, messages, model=None):
        raise OllamaModelNotFoundError("model not enabled")

    monkeypatch.setattr(OllamaClient, "chat", fail)
    resp = await async_client.post("/api/v1/vision/analyze", files=_file(PNG_BYTES))
    assert resp.status_code == 503
    assert resp.json()["error_code"] == "VISION_MODEL_UNAVAILABLE"


async def test_vision_rejects_non_vision_registry_model(
    async_client: AsyncClient, async_app: FastAPI
) -> None:
    """6E audit G1: model selection must pass the registry VISION gate — a
    registered but chat-only model must yield 503, never reach Ollama."""
    await _login(async_client, "p5e-f@verifytest.com")
    async_app.state.settings.vision_model = "qwen3:0.6b"  # registered, CHAT-only
    resp = await async_client.post("/api/v1/vision/analyze", files=_file(PNG_BYTES))
    assert resp.status_code == 503
    assert resp.json()["error_code"] == "VISION_MODEL_UNAVAILABLE"


async def test_voice_capabilities_reports_no_server_voice(async_client: AsyncClient) -> None:
    """ADR-016: server has no STT/TTS; clients use platform speech APIs."""
    await _login(async_client, "p5f-a@verifytest.com")
    resp = await async_client.get("/api/v1/voice/capabilities")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["server_stt"] is False and body["server_tts"] is False
    assert body["client_platform_voice"] is True


async def test_voice_capabilities_requires_auth(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/voice/capabilities")
    assert resp.status_code == 401
