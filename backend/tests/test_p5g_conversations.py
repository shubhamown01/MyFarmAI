"""P5G tests: conversation-history API + preferences — user-scoped, deny-by-default."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.conversation import Conversation, Message, MessageRole
from app.db.models.user import User
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")


async def _make_user(email: str) -> User:
    async with db_manager.session() as session:
        user = User(email=email, password_hash=hash_password("Pass-2026!x"))
        session.add(user)
        return user


async def _login(client: AsyncClient, email: str) -> None:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"})
    assert resp.status_code == 200, resp.text


async def _make_conversation_with_messages(user: User, n: int = 2) -> str:
    async with db_manager.session() as session:
        conv = Conversation(user_id=user.id, language="en", model_name="qwen3:0.6b")
        session.add(conv)
        await session.flush()
        for i in range(n):
            session.add(
                Message(
                    conversation_id=conv.id,
                    role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                    content=f"message {i}",
                )
            )
        return str(conv.id)


async def test_list_conversations_own_only(async_client: AsyncClient) -> None:
    a = await _make_user("p5g-a@example.com")
    b = await _make_user("p5g-b@example.com")
    await _make_conversation_with_messages(a)
    conv_b = await _make_conversation_with_messages(b)

    await _login(async_client, "p5g-a@example.com")
    items = (await async_client.get("/api/v1/conversations")).json()
    assert len(items) == 1
    assert all(c["id"] != conv_b for c in items)


async def test_conversation_detail_with_messages(async_client: AsyncClient) -> None:
    user = await _make_user("p5g-c@example.com")
    conv_id = await _make_conversation_with_messages(user, n=2)
    await _login(async_client, "p5g-c@example.com")

    resp = await async_client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == conv_id
    assert [m["content"] for m in body["messages"]] == ["message 0", "message 1"]
    assert body["messages"][0]["role"] in ("user", "assistant")


async def test_cross_user_conversation_404(async_client: AsyncClient) -> None:
    a = await _make_user("p5g-d@example.com")
    await _make_user("p5g-e@example.com")
    conv_id = await _make_conversation_with_messages(a)

    await _login(async_client, "p5g-e@example.com")
    resp = await async_client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "CONVERSATION_NOT_FOUND"


async def test_unauthenticated_401(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/conversations")
    assert resp.status_code == 401


async def test_preferences_update_and_persist(async_client: AsyncClient) -> None:
    await _make_user("p5g-f@example.com")
    await _login(async_client, "p5g-f@example.com")
    resp = await async_client.patch("/api/v1/auth/preferences", json={"preferred_language": "hi"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["preferred_language"] == "hi"
    # persisted
    me = (await async_client.get("/api/v1/auth/me")).json()
    assert me["preferred_language"] == "hi"


async def test_preferences_invalid_language_422(async_client: AsyncClient) -> None:
    await _make_user("p5g-g@example.com")
    await _login(async_client, "p5g-g@example.com")
    resp = await async_client.patch(
        "/api/v1/auth/preferences", json={"preferred_language": "HINDI"}
    )
    assert resp.status_code == 422


async def test_preferences_unauthenticated_401(async_client: AsyncClient) -> None:
    resp = await async_client.patch("/api/v1/auth/preferences", json={"preferred_language": "en"})
    assert resp.status_code == 401
