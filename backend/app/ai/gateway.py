"""AI gateway (P4-01): provider-independent interface.

Domain modules (chat, research) depend only on `AIGateway` and the shared
error types below. Ollama-specific HTTP behavior stays inside the adapter.
"""

from typing import Protocol

from app.services.ollama import OllamaClient


class AIError(Exception):
    """Base AI gateway error."""


class AITimeoutError(AIError):
    pass


class AIConnectionError(AIError):
    pass


class AIModelNotFoundError(AIError):
    pass


class AIBusyError(AIError):
    """Queue depth exceeded; request rejected before waiting for a slot."""


class AIGateway(Protocol):
    """Stable internal interface for chat completion (P4-01)."""

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str: ...

    async def health_check(self) -> bool: ...

    async def aclose(self) -> None: ...

    @property
    def model_name(self) -> str: ...


class OllamaGateway:
    """Ollama adapter; maps provider errors to gateway error types."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self._client = client or OllamaClient()

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        from app.ai.registry import require_enabled
        from app.services.ollama import (
            OllamaConnectionError,
            OllamaModelNotFoundError,
            OllamaTimeoutError,
        )

        # Registry check (Phase 4B): only for explicitly requested models.
        # The settings-level default is admin-controlled config and bypasses
        # the registry.
        if model is not None:
            require_enabled(model, "chat")
        try:
            return await self._client.chat(messages, model)
        except OllamaTimeoutError as e:
            raise AITimeoutError(str(e)) from e
        except OllamaConnectionError as e:
            raise AIConnectionError(str(e)) from e
        except OllamaModelNotFoundError as e:
            raise AIModelNotFoundError(str(e)) from e

    async def health_check(self) -> bool:
        return await self._client.health_check()

    async def aclose(self) -> None:
        await self._client.close()

    @property
    def model_name(self) -> str:
        return self._client.model


def _selected_provider(app_settings: object) -> str:
    """Resolve the effective provider from configuration.

    ``auto`` picks Gemini when a key is present and no local Ollama URL is
    configured (cloud), otherwise Ollama (local/desktop or disabled).
    """
    provider = str(getattr(app_settings, "ai_provider", "auto") or "auto").strip().lower()
    gemini_key = str(getattr(app_settings, "gemini_api_key", "") or "")
    ollama_url = str(getattr(app_settings, "ollama_base_url", "") or "")
    if provider == "gemini":
        return "gemini"
    if provider == "ollama":
        return "ollama"
    if gemini_key and not ollama_url:
        return "gemini"
    return "ollama"


def build_gateway(app_settings: object | None = None) -> AIGateway:
    """Build the configured AI gateway (Gemini or Ollama)."""
    if app_settings is None:
        from app.core.config import settings as app_settings

    if _selected_provider(app_settings) == "gemini":
        from app.ai.gemini import DEFAULT_BASE_URL, DEFAULT_MODEL, GeminiGateway

        return GeminiGateway(
            api_key=str(getattr(app_settings, "gemini_api_key", "")),
            model=str(getattr(app_settings, "gemini_model", DEFAULT_MODEL) or DEFAULT_MODEL),
            base_url=str(
                getattr(app_settings, "gemini_base_url", DEFAULT_BASE_URL) or DEFAULT_BASE_URL
            ),
            timeout=float(getattr(app_settings, "ollama_timeout_seconds", 60)),
        )
    return OllamaGateway()


ai_gateway: AIGateway = build_gateway()
