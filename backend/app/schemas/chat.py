from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The farmer's message or question",
    )
    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID to continue, or null to start new",
    )
    language: str = Field(
        default="en",
        pattern="^[a-z]{2}$",
        description="Language code (e.g., 'en', 'hi')",
    )
    crop: str | None = Field(
        default=None,
        max_length=100,
        description="Farmer's current crop for context",
    )
    location: str | None = Field(
        default=None,
        max_length=200,
        description="Farmer's location for localized advice",
    )

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant's response")
    conversation_id: str = Field(..., description="Conversation ID (new or continued)")
    model: str = Field(..., description="Model used for generation")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error description")
    error_code: str | None = Field(default=None, description="Machine-readable error code")
