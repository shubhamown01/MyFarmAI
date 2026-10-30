import os

import aiosqlite
from fastapi import Request

from app.core.config import settings


def _ensure_db_dir(db_path: str) -> None:
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


def _get_db_path(db_path: str | None = None, request: Request | None = None) -> str:
    """Get database path from explicit parameter, request state, or global settings."""
    if db_path:
        return db_path
    if request and hasattr(request.app.state, "database_path"):
        return request.app.state.database_path  # type: ignore[no-any-return]
    return settings.database_path


async def get_db_connection(
    db_path: str | None = None, request: Request | None = None
) -> aiosqlite.Connection:
    path = _get_db_path(db_path, request)
    _ensure_db_dir(path)
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db(db_path: str | None = None) -> None:
    path = _get_db_path(db_path)
    _ensure_db_dir(path)
    conn = await aiosqlite.connect(path)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language TEXT DEFAULT 'en',
                crop TEXT,
                location TEXT,
                is_archived BOOLEAN NOT NULL DEFAULT 0,
                message_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
            ON messages (conversation_id)
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id
            ON conversations (user_id)
            """
        )
        await conn.commit()
    finally:
        await conn.close()


def get_database_path(request: Request) -> str:
    """Get the database path from the request's app state."""
    if hasattr(request.app.state, "database_path"):
        return request.app.state.database_path  # type: ignore[no-any-return]
    return settings.database_path
