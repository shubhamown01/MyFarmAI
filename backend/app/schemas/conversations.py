"""Conversation-history API schemas (P5G)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Message PK is an Integer autoincrement (only Conversation is UUID-keyed).
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    language: str
    crop: str | None
    location: str | None
    farm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationSummaryResponse):
    messages: list[MessageResponse]
