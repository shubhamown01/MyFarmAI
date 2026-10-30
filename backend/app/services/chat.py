"""Chat service for generating AI responses using SQLAlchemy repositories."""

import asyncio
import contextlib
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.ai.gateway import (
    AIBusyError,
    AIConnectionError,
    AIError,
    AIModelNotFoundError,
    AITimeoutError,
    ai_gateway,
)

# Moved to app/ai/prompts.py (P4-05, versioned); re-exported for compatibility.
from app.ai.prompts import PROMPT_TEMPLATE_VERSION, build_system_prompt  # noqa: E402, F401
from app.db.models.conversation import MessageRole
from app.db.repositories import ConversationRepository, MessageRepository
from app.db.session import (
    db_manager,  # used by the sync test path
)
from app.services.ollama import (
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    ollama_client,
)


def _get_legacy_user_id() -> uuid.UUID:
    """Legacy user ID for pre-auth migrated conversations (no longer assigned to new chats)."""
    return uuid.UUID("00000000-0000-0000-0000-000000000000")


def generate_chat_response_sync(
    user_message: str,
    conversation_id: str | None = None,
    language: str = "en",
    crop: str | None = None,
    location: str | None = None,
    request: Request | None = None,
    db: Session | None = None,
    user_id: uuid.UUID | None = None,
    farm_context: dict | None = None,
) -> tuple[str, str]:
    """Generate a chat response and persist to database using synchronous SQLAlchemy (for tests)."""
    import concurrent.futures
    import logging

    logger = logging.getLogger("myfarmai.chat")

    try:
        from sqlalchemy import select

        from app.db.models.conversation import Conversation, Message, MessageRole

        # Use provided session or get a new one
        if db is not None:
            session = db
            owns_session = False
        else:
            # Fallback to getting a new session (for non-test usage)
            from app.db.session import get_db_session_sync

            session_gen = get_db_session_sync()
            session = next(session_gen)
            owns_session = True

        try:
            assert user_id is not None, "user_id is required (auth-gated endpoint)"

            if conversation_id:
                existing = session.execute(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.user_id == user_id)
                ).scalar_one_or_none()
                if not existing:
                    raise ValueError(f"Conversation {conversation_id} not found")
                conv_id: uuid.UUID = uuid.UUID(conversation_id)
            else:
                conversation = Conversation(
                    user_id=user_id,
                    language=language,
                    crop=crop,
                    location=location,
                    model_name="qwen3:0.6b",
                )
                session.add(conversation)
                session.flush()
                conv_id = conversation.id

            # Get recent messages
            recent_messages = (
                session.execute(
                    select(Message)
                    .where(Message.conversation_id == conv_id)
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                .scalars()
                .all()
            )

            messages = [
                {
                    "role": "system",
                    "content": build_system_prompt(language, crop, location, farm_context),
                }
            ]
            for msg in reversed(recent_messages):
                messages.append({"role": msg.role.value, "content": msg.content})
            messages.append({"role": "user", "content": user_message})

            # Persist user message
            user_msg = Message(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content=user_message,
            )
            session.add(user_msg)

            try:
                # Handle both running event loop and no event loop cases
                import asyncio

                try:
                    asyncio.get_running_loop()
                    # If we're in a running loop, we need to run the coroutine differently
                    # Since we're in a sync context, we can't await directly
                    # Use a new thread with its own event loop
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, ollama_client.chat(messages))
                        assistant_response = future.result(timeout=120)
                except RuntimeError:
                    # No running event loop, safe to use asyncio.run()
                    assistant_response = asyncio.run(ollama_client.chat(messages))
            except (OllamaTimeoutError, OllamaConnectionError, OllamaModelNotFoundError):
                error_msg = Message(
                    conversation_id=conv_id,
                    role=MessageRole.ASSISTANT,
                    content="I'm unable to reach the AI service right now. Please try again later.",
                )
                session.add(error_msg)
                session.flush()
                raise
            except OllamaError:
                error_msg = Message(
                    conversation_id=conv_id,
                    role=MessageRole.ASSISTANT,
                    # Generic persisted error text: raw exception strings can embed internal
                    # details (e.g. Ollama base_url) that would surface later
                    # through conversation history (4D exit-gate condition 3).
                    content="An error occurred while processing your request. Please try again.",
                )
                session.add(error_msg)
                session.flush()
                raise
            finally:
                # Ensure user message is committed
                session.flush()

            if not assistant_response or not assistant_response.strip():
                assistant_response = (
                    "I couldn't generate a response. Please try rephrasing your question."
                )

            # Persist assistant response
            assistant_msg = Message(
                conversation_id=conv_id,
                role=MessageRole.ASSISTANT,
                content=assistant_response,
            )
            session.add(assistant_msg)
            session.flush()

            return assistant_response, str(conv_id)
        except Exception as e:
            logger.exception("Error in generate_chat_response_sync: %s", e)
            raise
        finally:
            if owns_session:
                with contextlib.suppress(Exception):
                    session.close()
    finally:
        pass


async def generate_chat_response(
    user_message: str,
    conversation_id: str | None = None,
    language: str = "en",
    crop: str | None = None,
    location: str | None = None,
    request: Request | None = None,
    user_id: uuid.UUID | None = None,
    farm_context: dict | None = None,
) -> tuple[str, str]:
    """Generate a chat response and persist to database using SQLAlchemy repositories (async)."""
    import logging

    logger = logging.getLogger("myfarmai.chat")

    assert user_id is not None, "user_id is required (auth-gated endpoint)"
    # Convert conversation_id to UUID if provided
    conv_uuid: uuid.UUID | None = uuid.UUID(conversation_id) if conversation_id else None

    try:
        # asynccontextmanager commits on clean exit (including return);
        # `async for` over the dependency would skip the commit entirely.
        async with db_manager.session() as session:
            conv_repo = ConversationRepository(session)
            msg_repo = MessageRepository(session)

            if conv_uuid:
                existing = await conv_repo.get_by_id(conv_uuid, user_id)
                if not existing:
                    raise ValueError(f"Conversation {conversation_id} not found")
                conv_id = conv_uuid
            else:
                conversation = await conv_repo.create(
                    user_id=user_id,
                    language=language,
                    crop=crop,
                    location=location,
                    model_name="qwen3:0.6b",
                )
                conv_id = conversation.id

            recent_messages = await msg_repo.get_recent(conv_id, limit=10)
            messages = [
                {
                    "role": "system",
                    "content": build_system_prompt(language, crop, location, farm_context),
                }
            ]
            for msg in recent_messages:
                messages.append({"role": msg.role.value, "content": msg.content})
            messages.append({"role": "user", "content": user_message})

            # Persist user message
            await msg_repo.create(
                conversation_id=conv_id,
                role=MessageRole.USER,
                content=user_message,
            )

            try:
                # Concurrency bound (P3-12) + queue-depth bound (P4-02): cap
                # in-flight AI requests AND waiters; excess gets 503 AI_BUSY
                # instead of an unbounded wait (protects the 2 GiB VRAM host).
                from app.core.config import settings as app_settings

                if not hasattr(ai_gateway, "_gate"):
                    ai_gateway._gate = asyncio.Semaphore(  # type: ignore[attr-defined]
                        app_settings.ai_max_concurrent_requests
                    )
                gate = ai_gateway._gate  # type: ignore[attr-defined]
                waiting = getattr(ai_gateway, "_waiting", 0)
                if gate.locked() and waiting >= app_settings.ai_max_queue_depth:
                    raise AIBusyError("AI service is busy; try again shortly")
                # No await between check and increment (single event loop) — race-free.
                ai_gateway._waiting = waiting + 1  # type: ignore[attr-defined]
                try:
                    async with gate:
                        assistant_response = await ai_gateway.chat(messages)
                finally:
                    ai_gateway._waiting = getattr(ai_gateway, "_waiting", 1) - 1  # type: ignore[attr-defined]
            except (AITimeoutError, AIConnectionError, AIModelNotFoundError, AIBusyError):
                await msg_repo.create(
                    conversation_id=conv_id,
                    role=MessageRole.ASSISTANT,
                    content="I'm unable to reach the AI service right now. Please try again later.",
                )
                raise
            except AIError:
                await msg_repo.create(
                    conversation_id=conv_id,
                    role=MessageRole.ASSISTANT,
                    # Generic persisted error text: raw exception strings can embed internal
                    # details (e.g. Ollama base_url) that would surface later
                    # through conversation history (4D exit-gate condition 3).
                    content="An error occurred while processing your request. Please try again.",
                )
                raise

            if not assistant_response or not assistant_response.strip():
                assistant_response = (
                    "I couldn't generate a response. Please try rephrasing your question."
                )

            # Persist assistant response
            await msg_repo.create(
                conversation_id=conv_id,
                role=MessageRole.ASSISTANT,
                content=assistant_response,
            )

            return assistant_response, str(conv_id)
    except Exception as e:
        logger.exception("Error in generate_chat_response: %s", e)
        raise
    # This line should never be reached due to the return in try or raise in except
    # but mypy needs it for type checking
    return "", ""


async def get_conversation_history(
    conversation_id: str,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict[str, str]] | None:
    """Get conversation with messages for history display (ownership-scoped)."""
    conv_uuid = uuid.UUID(conversation_id)
    async with db_manager.session() as session:
        conv_repo = ConversationRepository(session)
        conversation = await conv_repo.get_by_id_with_messages(conv_uuid, user_id, limit=limit)
        if not conversation:
            return None
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in conversation.messages
        ]


async def list_user_conversations(
    user_id: str,
    limit: int = 20,
    farm_id: str | None = None,
) -> list[dict[str, str | int]]:
    """List conversations for a user."""
    user_uuid = uuid.UUID(user_id)
    farm_uuid = uuid.UUID(farm_id) if farm_id else None
    async with db_manager.session() as session:
        conv_repo = ConversationRepository(session)
        conversations = await conv_repo.get_user_conversations(
            user_uuid, limit=limit, farm_id=farm_uuid
        )
        return [
            {
                "id": str(conv.id),
                "language": conv.language,
                "crop": conv.crop or "",
                "location": conv.location or "",
                "message_count": conv.message_count,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            }
            for conv in conversations
        ]
