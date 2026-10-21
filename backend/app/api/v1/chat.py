"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat import generate_chat_response
from app.services.ollama import (
    OllamaConnectionError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
)

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        503: {"model": ErrorResponse, "description": "AI service unavailable"},
        504: {"model": ErrorResponse, "description": "AI service timeout"},
    },
)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    try:
        response_text, conversation_id = await generate_chat_response(
            user_message=chat_request.message,
            conversation_id=chat_request.conversation_id,
            language=chat_request.language,
            crop=chat_request.crop,
            location=chat_request.location,
            request=request,
        )
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            model=settings.ollama_model,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": str(e), "error_code": "CONVERSATION_NOT_FOUND"},
        ) from e
    except OllamaModelNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"detail": str(e), "error_code": "MODEL_NOT_FOUND"},
        ) from e
    except OllamaConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Cannot connect to AI service. Please try again later.",
                "error_code": "OLLAMA_CONNECTION_FAILED",
            },
        ) from e
    except OllamaTimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "detail": "AI service request timed out. Please try again.",
                "error_code": "OLLAMA_TIMEOUT",
            },
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
        ) from e
