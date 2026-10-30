"""Crop-cycle API tests (P5A-02): farm-scoped CRUD, status transitions, isolation."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User
from app.db.repositories import CropRepository
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


async def _seed_crop(name: str = "Tomato") -> str:
    async with db_manager.session() as session:
        crop = await CropRepository(session).create(name=name)
        return str(crop.id)


async def _make_farm(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/farms", json={"name": "Cycle Farm"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_cycle(client: AsyncClient, farm_id: str, crop_id: str, year: int = 2026) -> dict:
    resp = await client.post(
        f"/api/v1/farms/{farm_id}/crop-cycles",
        json={"crop_id": crop_id, "season_year": year, "area_hectares": 1.5},
    )
    return resp.json() | {"_status": resp.status_code}


async def test_create_cycle_201(async_client: AsyncClient) -> None:
    await _make_user("cc1@example.com")
    await _login(async_client, "cc1@example.com")
    crop_id = await _seed_crop()
    farm_id = await _make_farm(async_client)
    body = await _create_cycle(async_client, farm_id, crop_id)
    assert body["_status"] == 201, body
    assert body["status"] == "planned"
    assert body["season_year"] == 2026


async def test_duplicate_season_409(async_client: AsyncClient) -> None:
    await _make_user("cc2@example.com")
    await _login(async_client, "cc2@example.com")
    crop_id = await _seed_crop("Onion")
    farm_id = await _make_farm(async_client)
    first = await _create_cycle(async_client, farm_id, crop_id)
    assert first["_status"] == 201
    dup = await _create_cycle(async_client, farm_id, crop_id)
    assert dup["_status"] == 409
    assert dup["error_code"] == "CROP_CYCLE_CONFLICT"


async def test_unknown_crop_404(async_client: AsyncClient) -> None:
    await _make_user("cc3@example.com")
    await _login(async_client, "cc3@example.com")
    farm_id = await _make_farm(async_client)
    body = await _create_cycle(async_client, farm_id, "00000000-0000-0000-0000-000000000002")
    assert body["_status"] == 404
    assert body["error_code"] == "CROP_NOT_FOUND"


async def test_cross_user_cycle_404(async_client: AsyncClient) -> None:
    await _make_user("cc4@example.com")
    await _make_user("cc5@example.com")
    await _login(async_client, "cc4@example.com")
    crop_id = await _seed_crop("Mango")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)

    async_client.cookies.clear()
    await _login(async_client, "cc5@example.com")
    resp = await async_client.get(f"/api/v1/crop-cycles/{cycle['id']}")
    assert resp.status_code == 404
    # farm-scoped list is also empty for the outsider
    resp = await async_client.get(f"/api/v1/farms/{farm_id}/crop-cycles")
    assert resp.status_code == 404  # outsider isn't a farm member -> farm not found


async def test_list_filter_by_status(async_client: AsyncClient) -> None:
    await _make_user("cc6@example.com")
    await _login(async_client, "cc6@example.com")
    crop_id = await _seed_crop("Wheat")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)
    # transition planned -> planted
    resp = await async_client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "planted"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "planted"

    planted = (await async_client.get(f"/api/v1/farms/{farm_id}/crop-cycles?status=planted")).json()
    assert [c["id"] for c in planted] == [cycle["id"]]
    planned = (await async_client.get(f"/api/v1/farms/{farm_id}/crop-cycles?status=planned")).json()
    assert planned == []


async def test_invalid_status_transition_422(async_client: AsyncClient) -> None:
    await _make_user("cc7@example.com")
    await _login(async_client, "cc7@example.com")
    crop_id = await _seed_crop("Rice")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)
    resp = await async_client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "harvested"}
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "CROP_CYCLE_INVALID_TRANSITION"


async def test_archived_is_terminal(async_client: AsyncClient) -> None:
    await _make_user("cc8@example.com")
    await _login(async_client, "cc8@example.com")
    crop_id = await _seed_crop("Maize")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)
    resp = await async_client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "archived"}
    )
    assert resp.status_code == 200
    resp = await async_client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "planted"}
    )
    assert resp.status_code == 422


async def test_harvest_update_fields(async_client: AsyncClient) -> None:
    await _make_user("cc9@example.com")
    await _login(async_client, "cc9@example.com")
    crop_id = await _seed_crop("Millet")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)
    await async_client.patch(f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "planted"})
    await async_client.patch(f"/api/v1/crop-cycles/{cycle['id']}", json={"status": "growing"})
    resp = await async_client.patch(
        f"/api/v1/crop-cycles/{cycle['id']}",
        json={
            "status": "harvested",
            "actual_yield_kg": 4200.5,
            "actual_harvest_date": "2026-10-01",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["actual_yield_kg"] == 4200.5
    assert resp.json()["status"] == "harvested"


async def test_viewer_cannot_update_cycle(async_client: AsyncClient) -> None:
    await _make_user("cc10@example.com")
    viewer = await _make_user("cc11@example.com")
    await _login(async_client, "cc10@example.com")
    crop_id = await _seed_crop("Cotton")
    farm_id = await _make_farm(async_client)
    cycle = await _create_cycle(async_client, farm_id, crop_id)

    resp = await async_client.post(
        f"/api/v1/farms/{farm_id}/members",
        json={"user_id": str(viewer.id), "role": "viewer"},
    )
    assert resp.status_code == 201, resp.text

    async_client.cookies.clear()
    await _login(async_client, "cc11@example.com")
    resp = await async_client.patch(f"/api/v1/crop-cycles/{cycle['id']}", json={"notes": "nope"})
    assert resp.status_code == 403
    # read is allowed
    resp = await async_client.get(f"/api/v1/crop-cycles/{cycle['id']}")
    assert resp.status_code == 200
