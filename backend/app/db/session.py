"""Async database session management with SQLAlchemy 2."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings


class DatabaseManager:
    """Manages database engine and session lifecycle."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self, database_url: str | None = None) -> None:
        """Initialize the database engine and session factory.

        Args:
            database_url: Optional override for the database URL.
                          If not provided, constructs from settings.
        """
        if database_url is None:
            # Construct URL from settings
            if settings.database_path.startswith("postgresql"):
                database_url = settings.database_path
            elif settings.database_path == ":memory:":
                database_url = "sqlite+aiosqlite:///:memory:"
            else:
                database_url = f"sqlite+aiosqlite:///{settings.database_path}"

        # Engine configuration
        if database_url.startswith("postgresql"):
            self._engine = create_async_engine(
                database_url,
                pool_size=settings.db_pool_size if hasattr(settings, "db_pool_size") else 5,
                max_overflow=settings.db_max_overflow
                if hasattr(settings, "db_max_overflow")
                else 10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.environment == "development",
            )
        else:
            # SQLite configuration
            self._engine = create_async_engine(
                database_url,
                poolclass=NullPool,
                connect_args={"check_same_thread": False},
                echo=settings.environment == "development",
            )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
        return self._session_factory

    async def close(self) -> None:
        """Close the database engine and all connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic commit/rollback."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with explicit transaction control."""
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with db_manager.session() as session:
        yield session


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database transaction."""
    async with db_manager.transaction() as session:
        yield session


def init_db_manager(database_url: str | None = None) -> None:
    """Initialize the global database manager."""
    db_manager.initialize(database_url)


async def close_db_manager() -> None:
    """Close the global database manager."""
    await db_manager.close()
