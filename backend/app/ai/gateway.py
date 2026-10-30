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

    @property
    def model_name(self) -> str:
        return self._client.model


ai_gateway: AIGateway = OllamaGateway()
