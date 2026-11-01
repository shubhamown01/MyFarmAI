"""Dashboard endpoint tests (P7A-01): auth, ownership, fail-open weather."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.usefixtures("async_initialized_db")


@pytest.fixture(autouse=True)
async def _authed_client(async_client: AsyncClient, request):
    """Log in a fresh user before each test (resources-test pattern)."""
    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.session import db_manager

    email = f"dash-{abs(hash(request.node.nodeid)) % 10**10}@verifytest.com"
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("Pass-2026!x")))
    resp = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"}
    )
    assert resp.status_code == 200, resp.text
    async_client.owner_email = email  # type: ignore[attr-defined]
    return async_client


async def _make_farm_with_crops(owner_email: str) -> str:
    import datetime as dt

    from app.db.models.user import User
    from app.db.repositories import CropCycleRepository, CropRepository, FarmRepository
    from app.db.session import db_manager

    async with db_manager.session() as session:
        user_id = (
            await session.execute(
                __import__("sqlalchemy").select(User.id).where(User.email == owner_email)
            )
        ).scalar_one()
        farms = FarmRepository(session)
        farm = await farms.create(owner_id=str(user_id), name="Dash Farm")
        farm.latitude, farm.longitude = 28.61, 77.20
        crops = CropRepository(session)
        tomato = await crops.create(name="Tomato")
        await CropCycleRepository(session).create(
            farm_id=str(farm.id),
            crop_id=str(tomato.id),
            season_year=2026,
            status="planted",
            planting_date=dt.date(2026, 6, 1),
            expected_harvest_date=dt.date.today() + dt.timedelta(days=10),
        )
        return str(farm.id)


@pytest.mark.asyncio
async def test_dashboard_requires_auth(async_client: AsyncClient):
    async_client.cookies.clear()
    resp = await async_client.get(
        "/api/v1/dashboard", params={"farm_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_happy_path(async_client: AsyncClient):
    farm_id = await _make_farm_with_crops(async_client.owner_email)
    resp = await async_client.get("/api/v1/dashboard", params={"farm_id": farm_id})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["farm"]["name"] == "Dash Farm"
    assert data["farm"]["latitude"] == 28.61
    assert data["crops"]["available"] is True
    assert data["crops"]["cycles"][0]["crop"] == "Tomato"
    # Task derived from the real expected_harvest_date (10 days out).
    assert data["tasks"]["items"][0]["crop"] == "Tomato"
    assert data["recommendations"]["available"] is False
    assert "not available yet" in data["recommendations"]["unavailable_reason"]
    for block in ("farm", "crops", "tasks", "alerts", "activity"):
        assert data[block]["updated_at"]


@pytest.mark.asyncio
async def test_dashboard_weather_outage_fails_open(async_client: AsyncClient, monkeypatch):
    """Weather provider down → explicit unavailable block; dashboard still 200."""

    async def _boom(*a, **k):
        raise RuntimeError("provider down")

    monkeypatch.setattr("app.services.dashboard.weather_client.get_weather", _boom)
    farm_id = await _make_farm_with_crops(async_client.owner_email)
    resp = await async_client.get("/api/v1/dashboard", params={"farm_id": farm_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["weather"]["available"] is False
    assert data["weather"]["unavailable_reason"] == "Weather service unavailable"
    assert data["farm"]["available"] is True  # dashboard never blanks


@pytest.mark.asyncio
async def test_dashboard_no_coordinates_reports_unavailable(async_client: AsyncClient):
    from sqlalchemy import select

    from app.db.models.user import User
    from app.db.repositories import FarmRepository
    from app.db.session import db_manager

    async with db_manager.session() as session:
        user_id = (
            await session.execute(select(User.id).where(User.email == async_client.owner_email))
        ).scalar_one()
        farm = await FarmRepository(session).create(owner_id=str(user_id), name="Bare Farm")
        farm_id = str(farm.id)
    resp = await async_client.get("/api/v1/dashboard", params={"farm_id": farm_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["weather"]["available"] is False
    assert "no coordinates" in data["weather"]["unavailable_reason"]


@pytest.mark.asyncio
async def test_dashboard_non_member_404(async_client: AsyncClient):
    """A different user's farm is indistinguishable from a nonexistent one."""
    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.repositories import FarmRepository
    from app.db.session import db_manager

    async with db_manager.session() as session:
        other = User(email="other-dash@example.com", password_hash=hash_password("Pass-2026!x"))
        session.add(other)
        await session.flush()  # assign the UUID before referencing it
        farm = await FarmRepository(session).create(owner_id=str(other.id), name="Not Yours")
        farm_id = str(farm.id)
    resp = await async_client.get("/api/v1/dashboard", params={"farm_id": farm_id})
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "FARM_NOT_FOUND"
