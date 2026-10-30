from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.security import generate_session_id, hash_token
from app.db.models.session import Session as SessionModel
from app.db.models.user import User
from app.db.session import db_manager


def _login(client: TestClient) -> None:
    """Insert a user + valid session row and set the auth cookie on the client."""
    session_id = generate_session_id()
    with db_manager.sync_session() as session:  # type: ignore[union-attr]
        user = User(email="chat-user@example.com", password_hash="not-used")
        session.add(user)
        session.flush()
        session.add(
            SessionModel(
                user_id=user.id,
                session_id_hash=hash_token(session_id),
                expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
            )
        )
    client.cookies.set("myfarmai_session", session_id)


class TestChatEndpoint:
    def test_chat_creates_new_conversation(self, client: TestClient, mock_ollama_client):
        _login(client)
        response = client.post(
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

    def test_chat_requires_authentication(self, client: TestClient):
        response = client.post(
            "/api/v1/chat",
            json={"message": "What crop should I plant?"},
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "NOT_AUTHENTICATED"

    def test_chat_continues_existing_conversation(self, client: TestClient, mock_ollama_client):
        _login(client)
        # First request
        response1 = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )
        assert response1.status_code == 200
        conv_id = response1.json()["conversation_id"]

        # Second request with same conversation_id
        response2 = client.post(
            "/api/v1/chat",
            json={"message": "And for rice?", "conversation_id": conv_id},
        )
        assert response2.status_code == 200
        data = response2.json()
        assert data["conversation_id"] == conv_id

    def test_chat_rejects_invalid_conversation_id(self, client: TestClient, mock_ollama_client):
        _login(client)
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello", "conversation_id": "invalid-uuid"},
        )
        assert response.status_code == 422
        response.json()
        # Validation error for invalid UUID format

    def test_chat_validates_message_length(self, client: TestClient):
        _login(client)
        # Empty message
        response = client.post(
            "/api/v1/chat",
            json={"message": ""},
        )
        assert response.status_code == 422

        # Whitespace only
        response = client.post(
            "/api/v1/chat",
            json={"message": "   "},
        )
        assert response.status_code == 422

        # Too long
        long_message = "x" * 2001
        response = client.post(
            "/api/v1/chat",
            json={"message": long_message},
        )
        assert response.status_code == 422

    def test_chat_validates_language_code(self, client: TestClient):
        _login(client)
        # Invalid language code (too long)
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hi", "language": "eng"},
        )
        assert response.status_code == 422

        # Invalid language code (numbers)
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hi", "language": "en1"},
        )
        assert response.status_code == 422

    def test_chat_ollama_connection_error(self, client: TestClient):
        _login(client)
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaConnectionError

            mock.chat = AsyncMock(side_effect=OllamaConnectionError("Connection failed"))

            response = client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["error_code"] == "OLLAMA_CONNECTION_FAILED"

    def test_chat_ollama_timeout(self, client: TestClient):
        _login(client)
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaTimeoutError

            mock.chat = AsyncMock(side_effect=OllamaTimeoutError("Timeout"))

            response = client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 504
            data = response.json()
            assert data["error_code"] == "OLLAMA_TIMEOUT"

    def test_chat_ollama_model_not_found(self, client: TestClient):
        _login(client)
        with patch("app.services.chat.ollama_client") as mock:
            from app.services.ollama import OllamaModelNotFoundError

            mock.chat = AsyncMock(side_effect=OllamaModelNotFoundError("Model not found"))

            response = client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["error_code"] == "MODEL_NOT_FOUND"

    def test_chat_includes_optional_fields(self, client: TestClient, mock_ollama_client):
        _login(client)
        response = client.post(
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


class TestModel1Matrix:
    """Model 1 (qwen3:0.6b) acceptance matrix additions (Phase 4 master prompt §6)."""

    def test_chat_rejects_empty_message(self, client: TestClient):
        """Empty message → 422 (min_length=1)."""
        _login(client)
        response = client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_rejects_missing_message(self, client: TestClient):
        """Malformed request (no message field) → 422, flat error envelope."""
        _login(client)
        response = client.post("/api/v1/chat", json={"prompt": "hi"})
        assert response.status_code == 422

    def test_chat_rejects_oversized_message(self, client: TestClient):
        """Message > 2000 chars → 422."""
        _login(client)
        response = client.post("/api/v1/chat", json={"message": "x" * 2001})
        assert response.status_code == 422
