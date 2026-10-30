"""P3-14/P3-15: auth-matrix API-level cross-user test + async chat-write regression.

P3-14: cross-user conversation access at the API level → 404 (the repository
layer scoping is covered in test_conversation_ownership.py).
P3-15: async chat twin (`generate_chat_response`) persists both messages —
guards the FCL-019 data-loss class (async session commit semantics).
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.security import generate_session_id, hash_token
from app.db.models.session import Session as SessionModel
from app.db.models.user import User
from app.db.session import db_manager


def _insert_user_with_session(email: str) -> str:
    """Direct row insert (sync mode); returns the raw session id."""
    session_id = generate_session_id()
    with db_manager.sync_session() as session:  # type: ignore[union-attr]
        user = User(email=email, password_hash="not-used")
        session.add(user)
        session.flush()
        session.add(
            SessionModel(
                user_id=user.id,
                session_id_hash=hash_token(session_id),
                expires_at=(datetime.now(UTC) + timedelta(hours=1)).replace(tzinfo=None),
            )
        )
    return session_id


class TestCrossUserAccess:
    def test_cross_user_conversation_404(self, client: TestClient, mock_ollama_client):
        """User B cannot continue user A's conversation (API-level → 404)."""
        session_a = _insert_user_with_session("user-a@example.com")
        session_b = _insert_user_with_session("user-b@example.com")

        # User A creates a conversation.
        client.cookies.set("myfarmai_session", session_a)
        resp_a = client.post("/api/v1/chat", json={"message": "my crop question"})
        assert resp_a.status_code == 200
        conv_id = resp_a.json()["conversation_id"]

        # User B tries to continue it.
        client.cookies.set("myfarmai_session", session_b)
        resp_b = client.post(
            "/api/v1/chat",
            json={"message": "continue it", "conversation_id": conv_id},
        )
        assert resp_b.status_code == 404
        assert resp_b.json()["error_code"] == "CONVERSATION_NOT_FOUND"


class TestAsyncChatPersistence:
    async def test_async_chat_writes_survive_request(self, temp_db_path: str):
        """P3-15 regression: async chat twin persists user+assistant messages.

        Guards the FCL-019 class: `async for` over the session dependency
        skipped the commit; `async with db_manager.session()` must commit.
        """

        import app.services.chat as chat_mod
        from app.db.models.base import Base
        from app.db.models.conversation import Message as MessageModel
        from app.db.session import init_db_manager

        init_db_manager(f"sqlite+aiosqlite:///{temp_db_path}", async_mode=True)

        async def _init():
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        await _init()
        try:
            # Real user row for the FK.
            async with db_manager.session() as session:
                user = User(email="async-chat@example.com", password_hash="x")
                session.add(user)
                await session.flush()
                user_id = user.id

            with patch.object(chat_mod, "ai_gateway", new=AsyncMock()) as mock_gateway:
                mock_gateway.chat = AsyncMock(return_value="async ollama reply")
                # Queue-depth bookkeeping needs real ints (P4-02).
                mock_gateway._waiting = 0
                response, conversation_id = await chat_mod.generate_chat_response(
                    user_message="async persistence check",
                    user_id=user_id,
                )

            assert response == "async ollama reply"
            conv_uuid = uuid.UUID(conversation_id)

            # Messages must exist in a fresh session (committed, not rolled back).
            async with db_manager.session() as session:
                from sqlalchemy import select

                msgs = (
                    (
                        await session.execute(
                            select(MessageModel)
                            .where(MessageModel.conversation_id == conv_uuid)
                            .order_by(MessageModel.created_at)
                        )
                    )
                    .scalars()
                    .all()
                )
                assert [m.role.value for m in msgs] == ["user", "assistant"]
                assert msgs[0].content == "async persistence check"
                assert msgs[1].content == "async ollama reply"
        finally:
            await db_manager.close()
