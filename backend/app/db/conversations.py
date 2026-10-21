import uuid
from typing import Any

from app.db.connection import get_db_connection


async def create_conversation(
    language: str = "en",
    crop: str | None = None,
    location: str | None = None,
    db_path: str | None = None,
) -> str:
    conversation_id = str(uuid.uuid4())
    conn = await get_db_connection(db_path)
    try:
        await conn.execute(
            """
            INSERT INTO conversations (id, language, crop, location)
            VALUES (?, ?, ?, ?)
            """,
            (conversation_id, language, crop, location),
        )
        await conn.commit()
        return conversation_id
    finally:
        await conn.close()


async def get_conversation(
    conversation_id: str,
    db_path: str | None = None,
) -> dict[str, Any] | None:
    conn = await get_db_connection(db_path)
    try:
        cursor = await conn.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        await conn.close()


async def add_message(
    conversation_id: str,
    role: str,
    content: str,
    db_path: str | None = None,
) -> int:
    conn = await get_db_connection(db_path)
    try:
        cursor = await conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, role, content),
        )
        await conn.execute(
            """
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (conversation_id,),
        )
        await conn.commit()
        msg_id = cursor.lastrowid
        if msg_id is None:
            raise RuntimeError("Failed to get lastrowid after insert")
        return msg_id
    finally:
        await conn.close()


async def get_recent_messages(
    conversation_id: str,
    limit: int = 10,
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    if limit < 1 or limit > 50:
        limit = 10
    conn = await get_db_connection(db_path)
    try:
        cursor = await conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        )
        rows = list(await cursor.fetchall())
        return [dict(row) for row in list(reversed(rows))]
    finally:
        await conn.close()
