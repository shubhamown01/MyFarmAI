"""Conversation-history API (P5G): user-scoped list + detail with messages.

Read-only. The security boundary is the repository's P3-05 deny-by-default
user-scoped queries (ConversationRepository.get_user_conversations /
get_by_id_with_messages take the user_id and filter on it), so no separate
service layer is added — cross-user access looks like not-found.

Archived conversations: excluded from the list (repo filters is_archived),
but still retrievable by direct ID via detail — deliberate (history access
after archiving), matching get_by_id_with_messages semantics.
"""

import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.db.repositories import ConversationRepository
from app.db.session import db_manager
from app.schemas.conversations import (
    ConversationDetailResponse,
    ConversationSummaryResponse,
)

router = APIRouter(tags=["Conversations"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_conversation_repo(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[ConversationRepository]:
    async with db_manager.session() as session:
        yield ConversationRepository(session)


def _not_found():
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"detail": "conversation not found", "error_code": "CONVERSATION_NOT_FOUND"},
    )


@router.get("/conversations", response_model=list[ConversationSummaryResponse])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    repo: ConversationRepository = Depends(get_conversation_repo),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[ConversationSummaryResponse]:
    conversations = await repo.get_user_conversations(user_id, limit=limit)
    return [ConversationSummaryResponse.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    repo: ConversationRepository = Depends(get_conversation_repo),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ConversationDetailResponse:
    conversation = await repo.get_by_id_with_messages(conversation_id, user_id)
    if not conversation:
        raise _not_found()
    # get_by_id_with_messages returns messages sorted oldest-first (last 50).
    return ConversationDetailResponse.model_validate(conversation)
