"""Farmer profile + onboarding API tests (E5): upsert, computed state,
progression, pending-user visibility."""

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager

pytestmark = pytest.mark.usefixtures("async_initialized_db")


async def _make_user(email: str, verification_status: str = "active") -> User:
    async with db_manager.session() as session:
        user = User(
            email=email,
            password_hash=hash_password("Pass-2026!x"),
            verification_status=verification_status,
        )
        session.add(user)
        return user


async def _login(client: AsyncClient, email: str) -> None:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "Pass-2026!x"})
    assert resp.status_code == 200, resp.text


async def test_profile_upsert_and_completion(async_client: AsyncClient) -> None:
    await _make_user("prof-a@example.com")
    await _login(async_client, "prof-a@example.com")

    resp = await async_client.get("/api/v1/me/farmer-profile")
    assert resp.status_code == 404

    # Incomplete profile (missing farming_type).
    resp = await async_client.put("/api/v1/me/farmer-profile", json={"full_name": "Ravi Kumar"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["profile_completed"] is False

    # Adding farming_type completes it.
    resp = await async_client.put(
        "/api/v1/me/farmer-profile", json={"farming_type": "home_farming"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == "Ravi Kumar"  # upsert preserved earlier data
    assert body["profile_completed"] is True


async def test_profile_optional_fields_round_trip(async_client: AsyncClient) -> None:
    await _make_user("prof-b@example.com")
    await _login(async_client, "prof-b@example.com")
    resp = await async_client.put(
        "/api/v1/me/farmer-profile",
        json={
            "full_name": "Sita",
            "farming_type": "agricultural",
            "farming_experience_years": 12,
            "intended_crops": ["wheat", "mustard"],
            "soil_info": "alluvial",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["farming_experience_years"] == 12
    assert body["intended_crops"] == ["wheat", "mustard"]
    assert body["soil_info"] == "alluvial"


async def test_profile_invalid_farming_type_422(async_client: AsyncClient) -> None:
    await _make_user("prof-c@example.com")
    await _login(async_client, "prof-c@example.com")
    resp = await async_client.put(
        "/api/v1/me/farmer-profile", json={"farming_type": "industrial"}
    )
    assert resp.status_code == 422


async def test_onboarding_state_progression(async_client: AsyncClient) -> None:
    await _make_user("onb-a@example.com")
    await _login(async_client, "onb-a@example.com")

    resp = await async_client.get("/api/v1/me/onboarding")
    assert resp.status_code == 200, resp.text
    state = resp.json()
    by_step = {s["step"]: s["complete"] for s in state["steps"]}
    # Test-created user: verified contact (password admin-style account,
    # email_verified defaults False) — contact step incomplete.
    assert by_step["contact_verified"] is False
    assert state["next_step"] == "contact_verified"
    assert state["complete"] is False


async def test_onboarding_complete_after_profile(async_client: AsyncClient) -> None:
    """Full path for a verification-gated user: location + land + profile."""
    await _make_user("onb-b@example.com")
    await _login(async_client, "onb-b@example.com")

    r = await async_client.put(
        "/api/v1/me/home-location",
        json={"latitude": 28.61, "longitude": 77.20, "source": "manual_entry"},
    )
    assert r.status_code == 200
    farm = (await async_client.post("/api/v1/farms", json={"name": "F"})).json()
    r = await async_client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json={"name": "P", "land_type": "agricultural"},
    )
    assert r.status_code == 201
    r = await async_client.put(
        "/api/v1/me/farmer-profile",
        json={"full_name": "R", "farming_type": "agricultural"},
    )
    assert r.status_code == 200

    state = (await async_client.get("/api/v1/me/onboarding")).json()
    by_step = {s["step"]: s["complete"] for s in state["steps"]}
    assert by_step["location"] is True
    assert by_step["land"] is True
    assert by_step["profile"] is True
    assert state["next_step"] == "contact_verified"  # only email_verified missing


async def test_pending_user_onboarding_visible_but_profile_403(async_client: AsyncClient) -> None:
    await _make_user("onb-c@example.com", verification_status="pending_verification")
    await _login(async_client, "onb-c@example.com")

    resp = await async_client.get("/api/v1/me/onboarding")
    assert resp.status_code == 200
    assert resp.json()["verification_status"] == "pending_verification"

    resp = await async_client.put("/api/v1/me/farmer-profile", json={"full_name": "X"})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "USER_NOT_VERIFIED"


async def test_unauthenticated_onboarding_401(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/me/onboarding")
    assert resp.status_code == 401
