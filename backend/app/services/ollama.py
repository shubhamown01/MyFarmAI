import httpx

from app.core.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
    ) -> str:
        client = await self._get_client()
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            message = data.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            return ""
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Ollama request timed out after {self.timeout}s") from e
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
            ) from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaModelNotFoundError(
                    f"Model '{model or self.model}' not found in Ollama. Run: ollama pull {model or self.model}"
                ) from e
            raise OllamaError(f"Ollama API error: {e.response.status_code}") from e
        except Exception as e:
            raise OllamaError(f"Unexpected error calling Ollama: {e}") from e

    async def health_check(self) -> bool:
        client = await self._get_client()
        try:
            response = await client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class OllamaError(Exception):
    pass


class OllamaTimeoutError(OllamaError):
    pass


class OllamaConnectionError(OllamaError):
    pass


class OllamaModelNotFoundError(OllamaError):
    pass


ollama_client = OllamaClient()
