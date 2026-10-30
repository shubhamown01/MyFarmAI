"""P3-05: ownership predicates — cross-user access is denied by default."""

import uuid

import pytest

from app.db.models.user import User
from app.db.repositories import ConversationRepository
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")


async def _mk_user(email: str) -> User:
    async with db_manager.session() as session:
        user = User(email=email, password_hash="x")
        session.add(user)
        return user


@pytest.fixture(name="two_users")
async def two_users_fixture():
    return await _mk_user("a@example.com"), await _mk_user("b@example.com")


async def test_get_by_id_scoped(two_users):
    a, b = two_users
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(user_id=a.id)
        assert await repo.get_by_id(conv.id, a.id) is not None
        # Cross-user lookup looks like not-found.
        assert await repo.get_by_id(conv.id, b.id) is None


async def test_get_by_id_with_messages_scoped(two_users):
    a, b = two_users
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(user_id=a.id)
        assert await repo.get_by_id_with_messages(conv.id, a.id) is not None
        assert await repo.get_by_id_with_messages(conv.id, b.id) is None


async def test_update_context_scoped(two_users):
    a, b = two_users
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(user_id=a.id)
        assert await repo.update_context(conv.id, a.id, crop="wheat") is not None
        assert await repo.update_context(conv.id, b.id, crop="rice") is None


async def test_archive_and_delete_scoped(two_users):
    a, b = two_users
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        conv1 = await repo.create(user_id=a.id)
        conv2 = await repo.create(user_id=a.id)
        assert await repo.archive(conv1.id, b.id) is False  # foreign user cannot archive
        assert await repo.archive(conv1.id, a.id) is True
        assert await repo.delete(conv2.id, b.id) is False  # foreign user cannot delete
        assert await repo.delete(conv2.id, a.id) is True


async def test_user_isolation_in_listing(two_users):
    a, b = two_users
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        await repo.create(user_id=a.id)
        await repo.create(user_id=a.id)
        await repo.create(user_id=b.id)
        assert len(await repo.get_user_conversations(a.id)) == 2
        assert len(await repo.get_user_conversations(b.id)) == 1


async def test_legacy_conversations_not_visible_to_real_users(two_users):
    """Pre-auth rows attributed to the legacy UUID are not readable by real users."""
    a, _ = two_users
    legacy_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    async with db_manager.session() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(user_id=legacy_id)
        assert await repo.get_by_id(conv.id, a.id) is None


async def test_chat_context_bounded_to_recent_10(two_users):
    """Model 1 matrix (P4): only the 10 most recent messages become model context."""
    from app.db.models.conversation import MessageRole
    from app.db.repositories import ConversationRepository, MessageRepository

    (a, _b) = two_users
    async with db_manager.session() as session:
        conv = await ConversationRepository(session).create(user_id=a.id)
        for i in range(1, 13):
            await MessageRepository(session).create(
                conversation_id=conv.id,
                role=MessageRole.USER if i % 2 else MessageRole.ASSISTANT,
                content=f"m{i}",
            )
        msgs = await MessageRepository(session).get_recent(conv.id, limit=10)
        contents = [m.content for m in msgs]
        assert len(contents) == 10
        assert contents[0] == "m3" and contents[-1] == "m12"  # m1, m2 dropped
