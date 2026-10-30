"""Versioned prompt templates (P4-05).

System policy is separated from user content by construction: the system
prompt is built only from this template; user messages are appended as
separate role messages and never interpolated into the template.

Bump PROMPT_TEMPLATE_VERSION on any change to the template text; the
version identifies the policy in effect for a conversation. Persistence of
the version per conversation row is deferred (schema change needs an
owner-approved Alembic migration).
"""

PROMPT_TEMPLATE_VERSION = "1"

SYSTEM_PROMPT_TEMPLATE = """You are a knowledgeable agricultural assistant for farmers.

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
