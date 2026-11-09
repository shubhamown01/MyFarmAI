"""Feedback API schemas (E1): minimal-field submission envelope."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FeedbackRequest(BaseModel):
    category: str = Field(..., pattern="^(bug|feature|question|praise)$")
    message: str = Field(..., min_length=5, max_length=2000)
    email: EmailStr | None = None  # optional for owner reply; never validated when absent
    app_version: str | None = Field(default=None, max_length=32)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str | None = None
    category: str
    message: str
    app_version: str | None = None
    created_at: str | None = None
