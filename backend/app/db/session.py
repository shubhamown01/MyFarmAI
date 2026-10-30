"""Async database session management with SQLAlchemy 2."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


class DatabaseManager:
    """Manages database engine and session lifecycle (both async and sync)."""

    def __init__(self) -> None:
        self._async_engine: AsyncEngine | None = None
        self._sync_engine: Engine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._sync_session_factory: sessionmaker[Session] | None = None
        self._is_async: bool = True

    @property
    def is_initialized(self) -> bool:
        """Check if the database manager is already initialized."""
        return self._async_engine is not None or self._sync_engine is not None

    def initialize(self, database_url: str | None = None, *, async_mode: bool = True) -> None:
        """Initialize the database engine and session factory.

        Args:
            database_url: Optional override for the database URL.
                          If not provided, constructs from settings.
            async_mode: If True, creates async engine (default).
                        If False, creates synchronous engine for tests.
        """
        if database_url is None:
            # Construct URL from settings
            if settings.database_path.startswith("postgresql"):
                database_url = settings.database_path
            elif settings.database_path == ":memory:":
                database_url = "sqlite+aiosqlite:///:memory:"
            else:
                database_url = f"sqlite+aiosqlite:///{settings.database_path}"

        self._is_async = async_mode

        if not async_mode:
            # Synchronous engine for tests
            self._sync_engine = create_engine(
                database_url,
                poolclass=NullPool,
                connect_args={"check_same_thread": False}
                if database_url.startswith("sqlite")
                else {},
                echo=settings.environment == "development",
            )
            self._sync_session_factory = sessionmaker(
                bind=self._sync_engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            self._async_engine = None
            self._async_session_factory = None
            return

        # Async engine configuration (existing logic)
        if database_url.startswith("postgresql"):
            self._async_engine = create_async_engine(
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
            # SQLite async configuration
            self._async_engine = create_async_engine(
                database_url,
                poolclass=NullPool,
                connect_args={"check_same_thread": False},
                echo=settings.environment == "development",
            )

        from sqlalchemy.ext.asyncio import async_sessionmaker

        self._async_session_factory = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        self._sync_engine = None
        self._sync_session_factory = None

    @property
    def engine(self) -> AsyncEngine | Engine:
        """Return the appropriate engine based on mode."""
        if self._is_async:
            if self._async_engine is None:
                raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            return self._async_engine
        else:
            if self._sync_engine is None:
                raise RuntimeError(
                    "DatabaseManager not initialized in sync mode. Call initialize(async_mode=False) first."
                )
            return self._sync_engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession] | sessionmaker[Session]:
        """Return the appropriate session factory based on mode."""
        if self._is_async:
            if self._async_session_factory is None:
                raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            return self._async_session_factory
        else:
            if self._sync_session_factory is None:
                raise RuntimeError(
                    "DatabaseManager not initialized in sync mode. Call initialize(async_mode=False) first."
                )
            return self._sync_session_factory

    async def close(self) -> None:
        """Close the database engine and all connections."""
        if self._async_engine is not None:
            await self._async_engine.dispose()
            self._async_engine = None
        if self._sync_engine is not None:
            self._sync_engine.dispose()
            self._sync_engine = None
        self._async_session_factory = None
        self._sync_session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic commit/rollback."""
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async session() in sync mode. Use sync_session() instead."
            )
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        async with async_session_factory() as session:
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
        """Get an async database session with explicit transaction control."""
        if not self._is_async:
            raise RuntimeError(
                "Cannot use async transaction() in sync mode. Use sync_transaction() instead."
            )
        from sqlalchemy.ext.asyncio import async_sessionmaker

        async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        async with async_session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise

    @contextmanager
    def sync_session(self) -> Generator[Session, None, None]:
        """Get a synchronous database session with automatic commit/rollback."""
        if self._is_async:
            raise RuntimeError("Cannot use sync_session() in async mode. Use session() instead.")
        from sqlalchemy.orm import Session, sessionmaker

        sync_session_factory = sessionmaker(
            bind=self._sync_engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        with sync_session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    @contextmanager
    def sync_transaction(self) -> Generator[Session, None, None]:
        """Get a synchronous database session with explicit transaction control."""
        if self._is_async:
            raise RuntimeError(
                "Cannot use sync_transaction() in async mode. Use transaction() instead."
            )
        from sqlalchemy.orm import Session, sessionmaker

        with sessionmaker(
            bind=self._sync_engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )() as session:
            with session.begin():
                try:
                    yield session
                except Exception:
                    session.rollback()
                    raise


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database session."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session_factory = async_sessionmaker(
        bind=db_manager._async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session_sync() -> Generator[Session, None, None]:
    """FastAPI dependency for synchronous database session (for tests)."""
    if db_manager._is_async:
        raise RuntimeError("Cannot use sync session in async mode.")
    from sqlalchemy.orm import Session, sessionmaker

    sync_session_factory = sessionmaker(
        bind=db_manager._sync_engine,
        class_=Session,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    with sync_session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database transaction."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async with async_sessionmaker(
        bind=db_manager._async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


def init_db_manager(database_url: str | None = None, *, async_mode: bool = True) -> None:
    """Initialize the global database manager."""
    db_manager.initialize(database_url, async_mode=async_mode)


async def close_db_manager() -> None:
    """Close the global database manager."""
    await db_manager.close()
