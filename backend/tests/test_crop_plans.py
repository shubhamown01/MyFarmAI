"""Crop-plan endpoint tests (P7B-2): auth, farm-scoped 404, plan/task
lifecycle, revision history, user-task protection, milestone assumptions."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

pytestmark = pytest.mark.usefixtures("async_initialized_db")

PUBLISH_ERROR_CODES = ("FARM_NOT_FOUND", "FARM_FORBIDDEN", "CROP_PLAN_NOT_FOUND")


@pytest.fixture(autouse=True)
async def _authed_client(async_client: AsyncClient, request):
    """Log in a fresh user before each test (dashboard-test pattern)."""
    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.session import db_manager

    email = f"plan-{abs(hash(request.node.nodeid)) % 10**10}@verifytest.com"
    async with db_manager.session() as session:
        session.add(User(email=email, password_hash=hash_password("Pass-2026!x")))
    resp = await async_client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"}
    )
    assert resp.status_code == 200, resp.text
    async_client.owner_email = email  # type: ignore[attr-defined]
    return async_client


async def _make_farm_with_cycle(
    owner_email: str, *, growing_days: tuple[int, int] | None = (90, 120)
) -> str:
    """Farm (owner = the logged-in test user) + tomato crop + planted cycle."""
    import datetime as dt

    from app.db.models.crop import Crop
    from app.db.models.user import User
    from app.db.repositories import CropCycleRepository, FarmRepository
    from app.db.session import db_manager

    async with db_manager.session() as session:
        user_id = (
            await session.execute(select(User.id).where(User.email == owner_email))
        ).scalar_one()
        farm = await FarmRepository(session).create(owner_id=str(user_id), name="Plan Farm")
        tomato = Crop(
            name=f"Tomato-{farm.id}",
            growing_days_min=growing_days[0],
            growing_days_max=growing_days[1],
        )
        session.add(tomato)
        await session.flush()
        cycle = await CropCycleRepository(session).create(
            farm_id=str(farm.id),
            crop_id=str(tomato.id),
            season_year=2026,
            status="planted",
            planting_date=dt.date(2026, 6, 1),
        )
        return str(farm.id), str(cycle.id)


async def _create_plan(client: AsyncClient, farm_id: str, cycle_id: str, **overrides) -> dict:
    payload = {
        "crop_cycle_id": cycle_id,
        "variety": "Cherry",
        "planting_date": "2026-06-01",
        "tasks": [{"title": "Buy seeds", "due_date": "2026-05-25"}],
        **overrides,
    }
    resp = await client.post(f"/api/v1/farms/{farm_id}/crop-plans", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_create_requires_auth(async_client: AsyncClient):
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    async_client.cookies.clear()
    resp = await async_client.post(
        f"/api/v1/farms/{farm_id}/crop-plans", json={"crop_cycle_id": cycle_id}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_non_member_404(async_client: AsyncClient):
    """A different user's farm is indistinguishable from a nonexistent one."""
    from app.core.security import hash_password
    from app.db.models.user import User
    from app.db.repositories import FarmRepository
    from app.db.session import db_manager

    async with db_manager.session() as session:
        other = User(email="other-plan@example.com", password_hash=hash_password("Pass-2026!x"))
        session.add(other)
        await session.flush()
        farm = await FarmRepository(session).create(owner_id=str(other.id), name="Not Yours")
        farm_id = str(farm.id)
    resp = await async_client.post(f"/api/v1/farms/{farm_id}/crop-plans", json={})
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "FARM_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_get_plan_with_milestones_and_assumptions(async_client: AsyncClient):
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, cycle_id)

    assert plan["variety"] == "Cherry"
    assert plan["assumptions"]  # assumptions always present
    assert "generic growing-day ranges" in plan["assumptions"]
    titles = [m["title"] for m in plan["milestones"]]
    assert titles == [
        "Sowing / planting",
        "Expected harvest (earliest)",
        "Expected harvest (latest)",
    ]
    # 2026-06-01 + 90 min / 120 max growing days
    assert plan["milestones"][1]["date"] == "2026-08-30"
    assert plan["milestones"][2]["date"] == "2026-09-29"
    assert plan["tasks"][0]["title"] == "Buy seeds"
    assert plan["tasks"][0]["source"] == "user"

    resp = await async_client.get(f"/api/v1/crop-plans/{plan['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == plan["id"]


@pytest.mark.asyncio
async def test_create_without_cycle_has_no_milestones(async_client: AsyncClient):
    """No cycle linked → no milestones derived, never invented."""
    farm_id, _ = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, None)
    assert plan["milestones"] == []
    assert plan["assumptions"]


@pytest.mark.asyncio
async def test_create_cycle_from_other_farm_rejected(async_client: AsyncClient):
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    other_farm_id, _ = await _make_farm_with_cycle(async_client.owner_email)
    resp = await async_client.post(
        f"/api/v1/farms/{other_farm_id}/crop-plans", json={"crop_cycle_id": cycle_id}
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "CROP_PLAN_INVALID"


@pytest.mark.asyncio
async def test_patch_records_revision_with_snapshot(async_client: AsyncClient):
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, cycle_id)

    resp = await async_client.patch(f"/api/v1/crop-plans/{plan['id']}", json={"variety": "Roma"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["variety"] == "Roma"

    revs = (await async_client.get(f"/api/v1/crop-plans/{plan['id']}/revisions")).json()
    assert len(revs) == 2  # "plan created" + the patch
    assert revs[0]["summary"] == "plan created"
    # Snapshots capture the state BEFORE each change (append-only history).
    assert revs[0]["snapshot"]["variety"] == "Cherry"
    assert revs[1]["summary"] == "updated: variety"
    assert revs[1]["snapshot"]["variety"] == "Cherry"  # before Roma was applied
    # Current state has the new value:
    assert (await async_client.get(f"/api/v1/crop-plans/{plan['id']}")).json()["variety"] == "Roma"


@pytest.mark.asyncio
async def test_task_lifecycle_soft_cancel(async_client: AsyncClient):
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, cycle_id)

    resp = await async_client.post(
        f"/api/v1/crop-plans/{plan['id']}/tasks", json={"title": "Water seedlings"}
    )
    assert resp.status_code == 201, resp.text
    task = resp.json()
    assert task["source"] == "user"  # API-created tasks are always the farmer's
    assert task["status"] == "pending"

    resp = await async_client.patch(
        f"/api/v1/crop-plans/{plan['id']}/tasks/{task['id']}",
        json={"status": "cancelled"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"  # soft-cancel, still exists

    resp = await async_client.get(f"/api/v1/crop-plans/{plan['id']}")
    titles = {t["title"] for t in resp.json()["tasks"]}
    assert "Water seedlings" in titles  # history preserved, not hard-deleted


@pytest.mark.asyncio
async def test_user_tasks_never_overwritten_by_system(async_client: AsyncClient):
    """Task edits flow only from the farmer; source is immutable."""
    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, cycle_id)
    task = plan["tasks"][0]

    resp = await async_client.patch(
        f"/api/v1/crop-plans/{plan['id']}/tasks/{task['id']}",
        json={"title": "Buy hybrid seeds", "source": "suggested"},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["title"] == "Buy hybrid seeds"  # farmer's own edit applied
    assert updated["source"] == "user"  # system can never re-attribute


@pytest.mark.asyncio
async def test_viewer_cannot_modify_plan(async_client: AsyncClient):
    """Viewers read but never write (farm roles, ADR-008)."""
    from app.core.security import hash_password
    from app.db.models.farm import FarmMember, FarmRole
    from app.db.models.user import User
    from app.db.session import db_manager

    farm_id, cycle_id = await _make_farm_with_cycle(async_client.owner_email)
    plan = await _create_plan(async_client, farm_id, cycle_id)

    async with db_manager.session() as session:
        viewer = User(email="viewer-plan@example.com", password_hash=hash_password("Pass-2026!x"))
        session.add(viewer)
        await session.flush()
        user_id = (
            await session.execute(select(User.id).where(User.email == async_client.owner_email))
        ).scalar_one()
        session.add(FarmMember(farm_id=farm_id, user_id=str(viewer.id), role=FarmRole.VIEWER))
        await session.flush()
        assert user_id  # owner member exists

    # log out owner, log in viewer
    async_client.cookies.clear()
    await async_client.post(
        "/api/v1/auth/login", json={"email": "viewer-plan@example.com", "password": "Pass-2026!x"}
    )
    # viewer CAN read
    resp = await async_client.get(f"/api/v1/crop-plans/{plan['id']}")
    assert resp.status_code == 200
    # viewer CANNOT write
    resp = await async_client.patch(f"/api/v1/crop-plans/{plan['id']}", json={"variety": "Sneaky"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FARM_FORBIDDEN"
