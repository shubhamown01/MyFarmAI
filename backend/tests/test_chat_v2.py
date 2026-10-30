"""P5B chat wiring tests: farm_id on chat requests resolves authorized context."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
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


async def test_chat_with_foreign_farm_404(async_client: AsyncClient) -> None:
    """Context resolution is membership-scoped: another user's farm → 404."""
    await _make_user("p5b-owner@example.com")
    await _make_user("p5b-out@example.com")
    async with db_manager.session() as session:
        from app.db.repositories import FarmRepository

        farm = await FarmRepository(session).create(
            owner_id="00000000-0000-0000-0000-000000000000", name="X"
        )
        farm_id = str(farm.id)

    await _login(async_client, "p5b-out@example.com")
    resp = await async_client.post(
        "/api/v1/chat",
        json={"message": "hello", "farm_id": farm_id},
    )
    assert resp.status_code == 404, resp.text
    assert resp.json()["error_code"] == "FARM_NOT_FOUND"


async def test_chat_invalid_farm_id_422(async_client: AsyncClient) -> None:
    await _make_user("p5b-bad@example.com")
    await _login(async_client, "p5b-bad@example.com")
    resp = await async_client.post(
        "/api/v1/chat",
        json={"message": "hello", "farm_id": "not-a-uuid"},
    )
    assert resp.status_code == 422
