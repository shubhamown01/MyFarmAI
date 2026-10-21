import pytest

from app.db.connection import get_db_connection, init_db
from app.db.conversations import (
    add_message,
    create_conversation,
    get_conversation,
    get_recent_messages,
)


class TestDatabase:
    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self, test_settings, temp_db_path):
        await init_db(temp_db_path)
        conn = await get_db_connection(temp_db_path)
        try:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in await cursor.fetchall()}
            assert "conversations" in tables
            assert "messages" in tables
        finally:
            await conn.close()

    @pytest.mark.asyncio
    async def test_create_conversation(self, initialized_db, temp_db_path):
        conv_id = await create_conversation(
            language="hi", crop="wheat", location="Punjab", db_path=temp_db_path
        )
        assert conv_id is not None
        assert len(conv_id) == 36

        conv = await get_conversation(conv_id, db_path=temp_db_path)
        assert conv is not None
        assert conv["language"] == "hi"
        assert conv["crop"] == "wheat"
        assert conv["location"] == "Punjab"

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, initialized_db, temp_db_path):
        conv = await get_conversation("00000000-0000-0000-0000-000000000000", db_path=temp_db_path)
        assert conv is None

    @pytest.mark.asyncio
    async def test_add_message(self, initialized_db, temp_db_path):
        conv_id = await create_conversation(db_path=temp_db_path)
        msg_id = await add_message(conv_id, "user", "Hello", db_path=temp_db_path)
        assert msg_id == 1

        msg_id2 = await add_message(conv_id, "assistant", "Hi there!", db_path=temp_db_path)
        assert msg_id2 == 2

    @pytest.mark.asyncio
    async def test_get_recent_messages(self, initialized_db, temp_db_path):
        import asyncio

        conv_id = await create_conversation(db_path=temp_db_path)

        await add_message(conv_id, "user", "Message 1", db_path=temp_db_path)
        await asyncio.sleep(0.01)
        await add_message(conv_id, "assistant", "Response 1", db_path=temp_db_path)
        await asyncio.sleep(0.01)
        await add_message(conv_id, "user", "Message 2", db_path=temp_db_path)
        await asyncio.sleep(0.01)
        await add_message(conv_id, "assistant", "Response 2", db_path=temp_db_path)
        await asyncio.sleep(0.01)
        await add_message(conv_id, "user", "Message 3", db_path=temp_db_path)
        await asyncio.sleep(0.01)
        await add_message(conv_id, "assistant", "Response 3", db_path=temp_db_path)

        # Get last 3 messages - should return 3 messages
        messages = await get_recent_messages(conv_id, limit=3, db_path=temp_db_path)
        assert len(messages) == 3
        # All returned messages should be from the conversation
        assert all(m["role"] in ("user", "assistant") for m in messages)
        # Should contain 3 distinct messages
        assert len({m["content"] for m in messages}) == 3

    @pytest.mark.asyncio
    async def test_get_recent_messages_limit(self, initialized_db, temp_db_path):
        conv_id = await create_conversation(db_path=temp_db_path)

        for i in range(15):
            await add_message(conv_id, "user", f"Message {i}", db_path=temp_db_path)
            await add_message(conv_id, "assistant", f"Response {i}", db_path=temp_db_path)

        messages = await get_recent_messages(conv_id, limit=10, db_path=temp_db_path)
        assert len(messages) == 10

    @pytest.mark.asyncio
    async def test_message_isolation(self, initialized_db, temp_db_path):
        conv1 = await create_conversation(db_path=temp_db_path)
        conv2 = await create_conversation(db_path=temp_db_path)

        await add_message(conv1, "user", "Conv 1 message", db_path=temp_db_path)
        await add_message(conv2, "user", "Conv 2 message", db_path=temp_db_path)

        messages1 = await get_recent_messages(conv1, limit=10, db_path=temp_db_path)
        messages2 = await get_recent_messages(conv2, limit=10, db_path=temp_db_path)

        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0]["content"] == "Conv 1 message"
        assert messages2[0]["content"] == "Conv 2 message"

    @pytest.mark.asyncio
    async def test_limit_validation(self, initialized_db, temp_db_path):
        conv_id = await create_conversation(db_path=temp_db_path)

        # Limit too high
        messages = await get_recent_messages(conv_id, limit=100, db_path=temp_db_path)
        assert len(messages) == 0  # No messages, but should not error

        # Limit too low
        messages = await get_recent_messages(conv_id, limit=0, db_path=temp_db_path)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_conversation_updated_at(self, initialized_db, temp_db_path):
        conv_id = await create_conversation(db_path=temp_db_path)

        import asyncio

        await asyncio.sleep(0.01)  # Ensure timestamp difference

        await add_message(conv_id, "user", "Test", db_path=temp_db_path)

        conv = await get_conversation(conv_id, db_path=temp_db_path)
        assert conv["updated_at"] >= conv["created_at"]
