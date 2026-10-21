import pytest

from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(message="Hello")
        assert req.message == "Hello"
        assert req.conversation_id is None
        assert req.language == "en"
        assert req.crop is None
        assert req.location is None

    def test_valid_request_with_all_fields(self):
        req = ChatRequest(
            message="Test",
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
            language="hi",
            crop="wheat",
            location="Punjab",
        )
        assert req.language == "hi"
        assert req.crop == "wheat"
        assert req.location == "Punjab"

    def test_message_trimmed(self):
        req = ChatRequest(message="  Hello  ")
        assert req.message == "Hello"

    def test_empty_message_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="   ")

    def test_message_too_long_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="x" * 2001)

    def test_invalid_language_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="Hi", language="eng")
        with pytest.raises(ValueError):
            ChatRequest(message="Hi", language="en1")
        with pytest.raises(ValueError):
            ChatRequest(message="Hi", language="EN")

    def test_valid_language_accepted(self):
        req = ChatRequest(message="Hi", language="hi")
        assert req.language == "hi"
        req = ChatRequest(message="Hi", language="en")
        assert req.language == "en"

    def test_crop_too_long_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="Hi", crop="x" * 101)

    def test_location_too_long_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(message="Hi", location="x" * 201)


class TestChatResponse:
    def test_valid_response(self):
        resp = ChatResponse(
            response="Test response",
            conversation_id="123e4567-e89b-12d3-a456-426614174000",
            model="qwen3:4b",
        )
        assert resp.response == "Test response"
        assert resp.model == "qwen3:4b"


class TestErrorResponse:
    def test_valid_error(self):
        err = ErrorResponse(detail="Error message", error_code="TEST_ERROR")
        assert err.detail == "Error message"
        assert err.error_code == "TEST_ERROR"

    def test_error_without_code(self):
        err = ErrorResponse(detail="Error message")
        assert err.error_code is None
