"""Chat API endpoints."""

import logging
import uuid
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.db.session import db_manager, get_db_session_sync
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat import generate_chat_response
from app.services.context import FarmContextService
from app.services.farm import FarmNotFoundError, FarmService
from app.services.weather import weather_client

router = APIRouter(tags=["Chat"])

logger = logging.getLogger("myfarmai.chat_api")


def get_settings(request: Request) -> Settings:
    """Get the app's settings from the request state."""
    return request.app.state.settings  # type: ignore[no-any-return]


def get_db_session_optional() -> Generator[Session | None, None, None]:
    """Sync session in sync/test mode; None in async mode.

    The async path builds its own session via db_manager; yielding None there
    avoids the "Cannot use sync session in async mode" dependency crash.
    """
    if db_manager._is_async:
        yield None
        return
    yield from get_db_session_sync()


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Conversation not found"},
        503: {
            "model": ErrorResponse,
            "description": "AI service unavailable or overloaded (error_code=AI_BUSY when the queue depth limit is exceeded)",
        },
        504: {"model": ErrorResponse, "description": "AI service timeout"},
    },
)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    settings: Settings = Depends(get_settings),
    db: Session | None = Depends(get_db_session_optional),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChatResponse:
    # P5B: resolve authorized farm context (async mode only — the sync test
    # path uses sync sessions which FarmService cannot await).
    farm_context: dict | None = None
    weather: dict | None = None
    if chat_request.farm_id and db_manager._is_async:
        async with db_manager.session() as session:
            try:
                ctx = await FarmContextService(session, FarmService(session)).get_context(
                    str(user_id), chat_request.farm_id
                )
            except FarmNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"detail": "farm not found", "error_code": "FARM_NOT_FOUND"},
                ) from None
        farm_context = {
            "name": ctx.name,
            "address": ctx.address,
            "latitude": ctx.latitude,
            "longitude": ctx.longitude,
            "crops": ctx.active_crops,
        }
        # P5C: attach live weather when the farm has coordinates. Fail-open —
        # a weather outage must never block chat; the prompt then contains no
        # weather block and the model is instructed not to invent conditions.
        if farm_context.get("latitude") is not None and farm_context.get("longitude") is not None:
            try:
                weather = await weather_client.get_weather(
                    float(ctx.latitude), float(ctx.longitude), include_daily=False
                )
            except Exception:
                weather = None

    # Check if we're in test mode (synchronous database)
    is_test = settings.environment == "test" and settings.database_path.startswith("sqlite")

    try:
        if is_test:
            # Use synchronous version for tests
            from app.services.chat import generate_chat_response_sync

            response_text, conversation_id = generate_chat_response_sync(
                user_message=chat_request.message,
                conversation_id=chat_request.conversation_id,
                language=chat_request.language,
                crop=chat_request.crop,
                location=chat_request.location,
                request=request,
                db=db,
                user_id=user_id,
            )
        else:
            response_text, conversation_id = await generate_chat_response(
                user_message=chat_request.message,
                conversation_id=chat_request.conversation_id,
                language=chat_request.language,
                crop=chat_request.crop,
                location=chat_request.location,
                request=request,
                user_id=user_id,
                farm_context=farm_context,
                weather=weather,
            )
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            model=settings.ollama_model,
        )
    except ValueError as e:
        # ValueError here only means conversation-ownership lookup failed
        # (services/chat.py). Don't echo str(e) — future ValueErrors from
        # other internals must not leak to clients (SEC-P5-04).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "conversation not found", "error_code": "CONVERSATION_NOT_FOUND"},
        ) from e
    except Exception as e:
        from app.ai.gateway import (
            AIBusyError,
            AIConnectionError,
            AIModelNotFoundError,
            AITimeoutError,
        )
        from app.services.ollama import (
            OllamaConnectionError,
            OllamaModelNotFoundError,
            OllamaTimeoutError,
        )

        # Both error families: sync/test path raises Ollama errors, async/production
        # path raises gateway (AI*) errors (P4-01 gateway interface).
        if isinstance(e, OllamaModelNotFoundError | AIModelNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    # Generic text: str(e) would leak the ollama-pull hint and
                    # internal model tag inventory to clients (4D condition 3).
                    "detail": "The requested AI model is not available.",
                    "error_code": "MODEL_NOT_FOUND",
                },
            ) from e
        elif isinstance(e, AIBusyError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "AI service is busy. Please try again shortly.",
                    "error_code": "AI_BUSY",
                },
            ) from e
        elif isinstance(e, OllamaConnectionError | AIConnectionError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "detail": "Cannot connect to AI service. Please try again later.",
                    "error_code": "OLLAMA_CONNECTION_FAILED",
                },
            ) from e
        elif isinstance(e, OllamaTimeoutError | AITimeoutError):
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={
                    "detail": "AI service request timed out. Please try again.",
                    "error_code": "OLLAMA_TIMEOUT",
                },
            ) from e
        elif isinstance(e, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": str(e), "error_code": "CONVERSATION_NOT_FOUND"},
            ) from e
        else:
            # Log before sanitizing: an unexpected 500 must be diagnosable
            # from server logs without leaking str(e) to the client.
            logger.exception("Unhandled chat error: %s", type(e).__name__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "An unexpected error occurred", "error_code": "INTERNAL_ERROR"},
            ) from e
