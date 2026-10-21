from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_creates_new_conversation(
        self, async_client: AsyncClient, mock_ollama_client
    ):
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "What crop should I plant?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert "model" in data
        assert data["response"] == "Test response from mocked Ollama"
        assert len(data["conversation_id"]) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_chat_continues_existing_conversation(
        self, async_client: AsyncClient, mock_ollama_client
    ):
        # First request
        response1 = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )
        assert response1.status_code == 200
        conv_id = response1.json()["conversation_id"]

        # Second request with same conversation_id
        response2 = await async_client.post(
            "/api/v1/chat",
            json={"message": "And for rice?", "conversation_id": conv_id},
        )
        assert response2.status_code == 200
        data = response2.json()
        assert data["conversation_id"] == conv_id

    @pytest.mark.asyncio
    async def test_chat_rejects_invalid_conversation_id(
        self, async_client: AsyncClient, mock_ollama_client
    ):
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hello", "conversation_id": "invalid-uuid"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error_code"] == "CONVERSATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_chat_validates_message_length(self, async_client: AsyncClient):
        # Empty message
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": ""},
        )
        assert response.status_code == 422

        # Whitespace only
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "   "},
        )
        assert response.status_code == 422

        # Too long
        long_message = "x" * 2001
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": long_message},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_validates_language_code(self, async_client: AsyncClient):
        # Invalid language code (too long)
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hi", "language": "eng"},
        )
        assert response.status_code == 422

        # Invalid language code (numbers)
        response = await async_client.post(
            "/api/v1/chat",
            json={"message": "Hi", "language": "en1"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_ollama_connection_error(self, async_client: AsyncClient):
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaConnectionError

            mock.chat = AsyncMock(side_effect=OllamaConnectionError("Connection failed"))

            response = await async_client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error_code"] == "OLLAMA_CONNECTION_FAILED"

    @pytest.mark.asyncio
    async def test_chat_ollama_timeout(self, async_client: AsyncClient):
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaTimeoutError

            mock.chat = AsyncMock(side_effect=OllamaTimeoutError("Timeout"))

            response = await async_client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 504
            data = response.json()
            assert data["detail"]["error_code"] == "OLLAMA_TIMEOUT"

    @pytest.mark.asyncio
    async def test_chat_ollama_model_not_found(self, async_client: AsyncClient):
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaModelNotFoundError

            mock.chat = AsyncMock(side_effect=OllamaModelNotFoundError("Model not found"))

            response = await async_client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error_code"] == "MODEL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_chat_includes_optional_fields(
        self, async_client: AsyncClient, mock_ollama_client
    ):
        response = await async_client.post(
            "/api/v1/chat",
            json={
                "message": "Test",
                "language": "hi",
                "crop": "wheat",
                "location": "Punjab",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] is not None
