"""Pytest configuration and fixtures for hermetic testing."""

import os
import uuid
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.session import close_db_manager, db_manager, get_db_session_sync, init_db_manager
from app.factory import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for each test."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
def test_settings(temp_db_path: str) -> Settings:
    """Create test settings with file-based SQLite database."""
    return Settings(
        environment="test",
        database_path=f"sqlite:///{temp_db_path}",
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        ollama_timeout_seconds=5,
        weather_timeout_seconds=5,
        rate_limit_requests=1000,
        log_level="WARNING",
    )


@pytest.fixture(scope="function")
def async_test_settings(temp_db_path: str) -> Settings:
    """Create test settings with async SQLite database."""
    return Settings(
        environment="test",
        database_path=f"sqlite+aiosqlite:///{temp_db_path}",
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        ollama_timeout_seconds=5,
        weather_timeout_seconds=5,
        rate_limit_requests=1000,
        log_level="WARNING",
    )


@pytest.fixture(scope="function")
def initialized_db(test_settings: Settings) -> Settings:
    """Initialize the test database schema using synchronous SQLAlchemy."""
    from sqlalchemy.orm import sessionmaker

    init_db_manager(test_settings.database_path, async_mode=False)
    from app.db.models.base import Base
    from app.db.models.user import User
    from app.db.session import db_manager

    # Use the db_manager's sync engine for creating tables
    sync_engine = db_manager._sync_engine
    Base.metadata.create_all(sync_engine)

    # Create legacy user for backward compatibility
    SyncSession = sessionmaker(bind=sync_engine)
    with SyncSession() as session:
        legacy_user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            email="legacy@myfarmai.test",
            password_hash="",
            full_name="Legacy Import",
            preferred_language="en",
            timezone="UTC",
            is_active=True,
            role="USER",
        )
        existing = session.query(User).filter(User.id == legacy_user.id).first()
        if not existing:
            session.add(legacy_user)
            session.commit()

    yield test_settings
    close_db_manager()


@pytest.fixture(scope="function")
def async_initialized_db(async_test_settings: Settings) -> Settings:
    """Initialize the test database schema using async SQLAlchemy."""
    init_db_manager(async_test_settings.database_path, async_mode=True)
    from app.db.models.base import Base
    from app.db.session import db_manager

    async def _init():
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Create legacy user for backward compatibility
            from app.db.models.user import User

            legacy_user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                email="legacy@myfarmai.test",
                password_hash="",
                full_name="Legacy Import",
                preferred_language="en",
                timezone="UTC",
                is_active=True,
                role="USER",
            )
            from sqlalchemy import select

            async with db_manager.session_factory() as session:
                existing = await session.execute(select(User).where(User.id == legacy_user.id))
                if not existing.scalar_one_or_none():
                    session.add(legacy_user)
                    await session.commit()

    import asyncio

    asyncio.get_event_loop().run_until_complete(_init())
    yield async_test_settings
    asyncio.get_event_loop().run_until_complete(close_db_manager())


@pytest.fixture(scope="function")
def mock_ollama_client():
    """Mock the Ollama client for testing."""
    from unittest.mock import AsyncMock, patch

    with patch("app.services.chat.ollama_client") as mock:
        mock.chat = AsyncMock(return_value="Test response from mocked Ollama")
        yield mock


@pytest.fixture(scope="function")
def app(initialized_db: Settings):
    """Create a test app with isolated settings (sync mode)."""
    return create_app(initialized_db, test_mode=True)


@pytest.fixture(scope="function")
def async_app(async_initialized_db: Settings):
    """Create a test app with isolated settings (async mode)."""
    return create_app(async_initialized_db, test_mode=True)


class SharedSessionTestClient(TestClient):
    """TestClient that shares a single database session across all requests."""

    def __init__(self, app, **kwargs):
        super().__init__(app, raise_server_exceptions=True)
        self._shared_session = None
        self._sync_engine = db_manager._sync_engine
        from sqlalchemy.orm import sessionmaker

        self._session_factory = sessionmaker(
            bind=db_manager._sync_engine, expire_on_commit=False, autoflush=False, autocommit=False
        )
        self._shared_session = self._session_factory()

        # Override the get_db_session_sync dependency to use our shared session
        app.dependency_overrides[get_db_session_sync] = self._get_shared_session_generator

    def _get_shared_session_generator(self):
        """Generator that yields the shared session."""
        if self._shared_session is None:
            from sqlalchemy.orm import sessionmaker

            self._shared_session = sessionmaker(
                bind=db_manager._sync_engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )()
        yield self._shared_session

    def close(self):
        if self._shared_session:
            self._shared_session.close()
            self._shared_session = None
        super().close()


@pytest.fixture(scope="function")
def client(app) -> Generator[TestClient, None, None]:
    """Create a synchronous test client for the app that shares a database session."""
    client = SharedSessionTestClient(app, raise_server_exceptions=True)
    yield client
    client.close()


@pytest.fixture(scope="function")
async def async_client(async_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the app with lifespan support."""
    transport = ASGITransport(app=async_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
