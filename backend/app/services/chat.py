"""Chat service for generating AI responses."""

from fastapi import Request

from app.db.conversations import (
    add_message,
    create_conversation,
    get_conversation,
    get_recent_messages,
)
from app.services.ollama import (
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    ollama_client,
)

SYSTEM_PROMPT_TEMPLATE = """You are an agricultural assistant for farmers. Provide helpful, accurate, and practical farming advice.

Guidelines:
- Give clear, actionable recommendations when possible.
- Acknowledge uncertainty; do not invent weather, market prices, or government scheme details.
- When advice depends on local conditions (soil, climate, pests), emphasize the need for local verification.
- Keep responses concise but complete.
- Use the farmer's language: {language}.
- If crop is specified ({crop}), tailor advice to that crop.
- If location is specified ({location}), consider regional context.

Response language: {language}."""


def build_system_prompt(language: str, crop: str | None, location: str | None) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        language=language,
        crop=crop or "not specified",
        location=location or "not specified",
    )


async def generate_chat_response(
    user_message: str,
    conversation_id: str | None = None,
    language: str = "en",
    crop: str | None = None,
    location: str | None = None,
    request: Request | None = None,
) -> tuple[str, str]:
    if conversation_id:
        existing = await get_conversation(conversation_id, request=request)
        if not existing:
            raise ValueError(f"Conversation {conversation_id} not found")
        conv_id = conversation_id
    else:
        conv_id = await create_conversation(
            language=language, crop=crop, location=location, request=request
        )

    recent_messages = await get_recent_messages(conv_id, limit=10, request=request)
    messages = [{"role": "system", "content": build_system_prompt(language, crop, location)}]
    for msg in recent_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    await add_message(conv_id, "user", user_message, request=request)

    try:
        assistant_response = await ollama_client.chat(messages)
    except (OllamaTimeoutError, OllamaConnectionError, OllamaModelNotFoundError):
        await add_message(
            conv_id,
            "assistant",
            "I'm unable to reach the AI service right now. Please try again later.",
            request=request,
        )
        raise
    except OllamaError as e:
        await add_message(conv_id, "assistant", f"An error occurred: {e}", request=request)
        raise

    if not assistant_response or not assistant_response.strip():
        assistant_response = "I couldn't generate a response. Please try rephrasing your question."

    await add_message(conv_id, "assistant", assistant_response, request=request)

    return assistant_response, conv_id
