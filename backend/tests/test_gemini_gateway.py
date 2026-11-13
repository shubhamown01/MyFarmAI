"""Gemini gateway adapter tests — mocked HTTP, no network."""

import httpx
import pytest

from app.ai.gateway import (
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    AITimeoutError,
    OllamaGateway,
    build_gateway,
)
from app.ai.gemini import GeminiGateway


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self._request = httpx.Request("POST", "https://example.test/chat/completions")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=self._request,
                response=httpx.Response(self.status_code, request=self._request),
            )

    def json(self) -> dict:
        return self._payload


class FakeAsyncClient:
    def __init__(self, response: FakeResponse | None = None, exc: Exception | None = None):
        self.response = response or FakeResponse()
        self.exc = exc
        self.posts: list[dict] = []
        self.gets: list[str] = []
        self.is_closed = False

    async def post(self, url: str, json: dict | None = None, headers: dict | None = None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        if self.exc:
            raise self.exc
        return self.response

    async def get(self, url: str, timeout: float | None = None, headers: dict | None = None):
        self.gets.append(url)
        if self.exc:
            raise self.exc
        return self.response

    async def aclose(self) -> None:
        self.is_closed = True


def _gateway(client: FakeAsyncClient) -> GeminiGateway:
    return GeminiGateway(api_key="test-key", model="gemini-2.0-flash", client=client)


async def test_chat_success_returns_content():
    client = FakeAsyncClient(
        FakeResponse(200, {"choices": [{"message": {"content": "hello farmer"}}]})
    )
    gateway = _gateway(client)

    assert await gateway.chat([{"role": "user", "content": "hi"}]) == "hello farmer"
    assert client.posts[0]["json"]["model"] == "gemini-2.0-flash"
    assert client.posts[0]["headers"]["Authorization"] == "Bearer test-key"


async def test_chat_empty_choices_returns_empty_string():
    client = FakeAsyncClient(FakeResponse(200, {"choices": []}))
    assert await _gateway(client).chat([{"role": "user", "content": "hi"}]) == ""


async def test_timeout_maps_to_ai_timeout():
    client = FakeAsyncClient(exc=httpx.TimeoutException("slow"))
    with pytest.raises(AITimeoutError):
        await _gateway(client).chat([{"role": "user", "content": "hi"}])


async def test_connect_error_maps_to_ai_connection_error():
    client = FakeAsyncClient(exc=httpx.ConnectError("refused"))
    with pytest.raises(AIConnectionError):
        await _gateway(client).chat([{"role": "user", "content": "hi"}])


async def test_404_maps_to_model_not_found():
    client = FakeAsyncClient(FakeResponse(404, {}))
    with pytest.raises(AIModelNotFoundError):
        await _gateway(client).chat([{"role": "user", "content": "hi"}])


async def test_429_maps_to_ai_error():
    client = FakeAsyncClient(FakeResponse(429, {}))
    with pytest.raises(AIError):
        await _gateway(client).chat([{"role": "user", "content": "hi"}])


async def test_health_check_uses_models_endpoint():
    client = FakeAsyncClient(FakeResponse(200, {"data": []}))
    assert await _gateway(client).health_check() is True
    assert client.gets == ["/models"]


async def test_aclose_closes_client():
    client = FakeAsyncClient()
    gateway = _gateway(client)
    await gateway.aclose()
    assert client.is_closed is True


class _Settings:
    def __init__(self, **over):
        self.ai_provider = "auto"
        self.gemini_api_key = ""
        self.gemini_model = "gemini-2.0-flash"
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_timeout_seconds = 60
        for key, value in over.items():
            setattr(self, key, value)


def test_build_gateway_auto_selects_gemini_on_cloud():
    gateway = build_gateway(_Settings(ai_provider="auto", gemini_api_key="key", ollama_base_url=""))
    assert isinstance(gateway, GeminiGateway)


def test_build_gateway_auto_keeps_ollama_when_configured():
    gateway = build_gateway(
        _Settings(ai_provider="auto", gemini_api_key="", ollama_base_url="http://localhost:11434")
    )
    assert isinstance(gateway, OllamaGateway)


def test_build_gateway_forces_provider():
    assert isinstance(
        build_gateway(_Settings(ai_provider="gemini", gemini_api_key="key")),
        GeminiGateway,
    )
    assert isinstance(
        build_gateway(_Settings(ai_provider="ollama", gemini_api_key="key")),
        OllamaGateway,
    )
