"""Pytest configuration and fixtures for hermetic testing."""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.db.connection import init_db
from app.factory import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def temp_db_path() -> AsyncGenerator[str, None]:
    """Create a temporary database file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
async def test_settings(temp_db_path: str) -> Settings:
    """Create test settings with isolated database."""
    return Settings(
        environment="test",
        database_path=temp_db_path,
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        ollama_timeout_seconds=5,
        weather_timeout_seconds=5,
        rate_limit_requests=1000,
        log_level="WARNING",
    )


@pytest.fixture(scope="function")
async def initialized_db(test_settings: Settings) -> Settings:
    """Initialize the test database schema."""
    await init_db(test_settings.database_path)
    return test_settings


@pytest.fixture(scope="function")
def mock_ollama_client():
    """Mock the Ollama client for testing."""
    from unittest.mock import AsyncMock, patch

    with patch("app.services.chat.ollama_client") as mock:
        mock.chat = AsyncMock(return_value="Test response from mocked Ollama")
        yield mock


@pytest.fixture(scope="function")
def app(initialized_db: Settings):
    """Create a test app with isolated settings."""
    return create_app(initialized_db)


@pytest.fixture(scope="function")
def client(app) -> TestClient:
    """Create a test client for the app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the app with lifespan support."""
    # Use TestClient to trigger lifespan, then use ASGITransport for async requests
    with TestClient(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
