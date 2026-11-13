"""Hosted AI gateway adapter (Gemini OpenAI-compatible endpoint).

The domain modules depend only on the :class:`app.ai.gateway.AIGateway`
protocol, so a second adapter is selected by configuration without touching
chat/research call sites.

Provider: Google Gemini free tier. The OpenAI-compatible surface is used so the
adapter stays small and provider-independent:

    POST {base_url}/chat/completions
    Authorization: Bearer <api_key>

Secrets never reach logs: only the exception type name is logged.
"""

from __future__ import annotations

import httpx

from app.ai.gateway import (
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    AITimeoutError,
)

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiGateway:
    """Gemini adapter implementing the internal AIGateway protocol."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self.model = model or DEFAULT_MODEL
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self._timeout),
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        client = await self._get_client()
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            response = await client.post(
                "/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            return ""
        except httpx.TimeoutException as exc:
            raise AITimeoutError(f"AI request timed out after {self._timeout}s") from exc
        except httpx.ConnectError as exc:
            raise AIConnectionError(f"Cannot connect to AI provider at {self.base_url}") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                raise AIModelNotFoundError(
                    f"Model '{model or self.model}' not found at the AI provider"
                ) from exc
            if status == 429:
                # Rate limited: surface as busy so the caller can retry later.
                from app.ai.gateway import AIBusyError

                raise AIBusyError("AI provider rate limit reached") from exc
            raise AIError(f"AI provider HTTP error: {status}") from exc
        except Exception as exc:
            raise AIError(f"Unexpected error calling AI provider: {type(exc).__name__}") from exc

    async def health_check(self) -> bool:
        client = await self._get_client()
        try:
            response = await client.get(
                "/models",
                timeout=5.0,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            return response.status_code == 200
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self.model
