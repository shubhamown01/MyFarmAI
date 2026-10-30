"""Farm API tests (P5A-01): CRUD, membership roles, cross-user 404 isolation."""

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


async def _create_farm(client: AsyncClient, name: str = "North Field") -> dict:
    resp = await client.post(
        "/api/v1/farms",
        json={"name": name, "latitude": 28.61, "longitude": 77.20},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_farm_201_owner_membership(async_client: AsyncClient) -> None:
    user = await _make_user("owner1@example.com")
    await _login(async_client, "owner1@example.com")
    farm = await _create_farm(async_client)
    assert farm["owner_id"] == str(user.id)
    assert farm["latitude"] == 28.61

    members = (await async_client.get(f"/api/v1/farms/{farm['id']}/members")).json()
    assert any(m["user_id"] == str(user.id) and m["role"] == "owner" for m in members)


async def test_unauthenticated_401(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/farms")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "NOT_AUTHENTICATED"


async def test_list_shows_only_own_farms(async_client: AsyncClient) -> None:
    await _make_user("list-a@example.com")
    await _make_user("list-b@example.com")
    await _login(async_client, "list-a@example.com")
    farm = await _create_farm(async_client, "Farm A")

    async_client.cookies.clear()  # switch user
    await _login(async_client, "list-b@example.com")
    farms = (await async_client.get("/api/v1/farms")).json()
    assert farms == []
    resp = await async_client.get(f"/api/v1/farms/{farm['id']}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "FARM_NOT_FOUND"


async def test_cross_user_patch_404(async_client: AsyncClient) -> None:
    await _make_user("own-a@example.com")
    await _make_user("own-b@example.com")
    await _login(async_client, "own-a@example.com")
    farm = await _create_farm(async_client, "Private Farm")

    async_client.cookies.clear()
    await _login(async_client, "own-b@example.com")
    resp = await async_client.patch(f"/api/v1/farms/{farm['id']}", json={"name": "Hijacked"})
    assert resp.status_code == 404
    # Confirm the farm was not modified.
    async_client.cookies.clear()
    await _login(async_client, "own-a@example.com")
    reread = (await async_client.get(f"/api/v1/farms/{farm['id']}")).json()
    assert reread["name"] == "Private Farm"


async def test_update_farm_fields(async_client: AsyncClient) -> None:
    await _make_user("upd@example.com")
    await _login(async_client, "upd@example.com")
    farm = await _create_farm(async_client, "Old Name")
    resp = await async_client.patch(
        f"/api/v1/farms/{farm['id']}",
        json={"name": "New Name", "description": "mango orchard"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "New Name"
    assert body["description"] == "mango orchard"


async def test_validation_lat_lon_422(async_client: AsyncClient) -> None:
    await _make_user("val@example.com")
    await _login(async_client, "val@example.com")
    for lat, lon in [(91.0, 0.0), (0.0, -181.0)]:
        resp = await async_client.post(
            "/api/v1/farms", json={"name": "x", "latitude": lat, "longitude": lon}
        )
        assert resp.status_code == 422, str(lat)


async def test_viewer_read_only(async_client: AsyncClient) -> None:
    await _make_user("vw-owner@example.com")
    viewer = await _make_user("vw-member@example.com")
    await _login(async_client, "vw-owner@example.com")
    farm = await _create_farm(async_client, "Shared Farm")

    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": str(viewer.id), "role": "viewer"},
    )
    assert resp.status_code == 201, resp.text

    async_client.cookies.clear()
    await _login(async_client, "vw-member@example.com")
    # Viewer can read…
    assert (await async_client.get(f"/api/v1/farms/{farm['id']}")).status_code == 200
    # …but not update.
    resp = await async_client.patch(f"/api/v1/farms/{farm['id']}", json={"name": "Nope"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FARM_FORBIDDEN"


async def test_member_management_owner_only(async_client: AsyncClient) -> None:
    await _make_user("mm-owner@example.com")
    member = await _make_user("mm-member@example.com")
    outsider = await _make_user("mm-out@example.com")
    await _login(async_client, "mm-owner@example.com")
    farm = await _create_farm(async_client, "Managed Farm")

    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": str(member.id), "role": "member"},
    )
    assert resp.status_code == 201, resp.text
    member_id = resp.json()["id"]

    # Member cannot add members (owner-only).
    async_client.cookies.clear()
    await _login(async_client, "mm-member@example.com")
    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": str(outsider.id), "role": "viewer"},
    )
    assert resp.status_code == 403

    # Owner changes the member's role to viewer.
    async_client.cookies.clear()
    await _login(async_client, "mm-owner@example.com")
    resp = await async_client.patch(
        f"/api/v1/farms/{farm['id']}/members/{member.id}", json={"role": "viewer"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "viewer"

    # Owner removes the member.
    resp = await async_client.delete(f"/api/v1/farms/{farm['id']}/members/{member.id}")
    assert resp.status_code == 204
    members = (await async_client.get(f"/api/v1/farms/{farm['id']}/members")).json()
    assert all(m["id"] != member_id for m in members)


async def test_add_unknown_user_404(async_client: AsyncClient) -> None:
    await _make_user("au@example.com")
    await _login(async_client, "au@example.com")
    farm = await _create_farm(async_client, "Solo Farm")
    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": "00000000-0000-0000-0000-000000000001", "role": "member"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "USER_NOT_FOUND"


async def test_cannot_remove_owner(async_client: AsyncClient) -> None:
    owner = await _make_user("ro@example.com")
    await _login(async_client, "ro@example.com")
    farm = await _create_farm(async_client, "Keeper Farm")
    resp = await async_client.delete(f"/api/v1/farms/{farm['id']}/members/{owner.id}")
    assert resp.status_code == 403
    # Owner membership is intact.
    members = (await async_client.get(f"/api/v1/farms/{farm['id']}/members")).json()
    assert any(m["user_id"] == str(owner.id) and m["role"] == "owner" for m in members)


async def test_create_farm_audits_event(async_client: AsyncClient) -> None:
    """Farm changes emit audit events (P5A-01) — ID-only, no coordinates."""
    user = await _make_user("audit@example.com")
    await _login(async_client, "audit@example.com")
    farm = await _create_farm(async_client, "Audited Farm")
    async with db_manager.session() as session:
        from sqlalchemy import select

        from app.db.models.audit import AuditEvent

        rows = (
            (
                await session.execute(
                    select(AuditEvent).where(AuditEvent.event_type == "farm_created")
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert str(rows[0].actor_id) == str(user.id)
    assert str(rows[0].subject_id) == farm["id"]


async def test_member_cannot_deactivate_farm(async_client: AsyncClient) -> None:
    """Security fix (FCL-049): is_active is owner-only — members cannot deactivate."""
    await _make_user("ia-owner@example.com")
    member = await _make_user("ia-member@example.com")
    await _login(async_client, "ia-owner@example.com")
    farm = await _create_farm(async_client, "Doomed Farm")
    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": str(member.id), "role": "member"},
    )
    assert resp.status_code == 201, resp.text

    async_client.cookies.clear()
    await _login(async_client, "ia-member@example.com")
    resp = await async_client.patch(f"/api/v1/farms/{farm['id']}", json={"is_active": False})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FARM_FORBIDDEN"


async def test_owner_grant_rejected_422(async_client: AsyncClient) -> None:
    other = await _make_user("og2@example.com")
    await _make_user("og@example.com")
    await _login(async_client, "og@example.com")
    farm = await _create_farm(async_client, "Grant Farm")
    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": str(other.id), "role": "owner"},
    )
    assert resp.status_code == 422
