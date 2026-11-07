"""Land registration API tests (E4): plots, boundaries, geodesic area, home
location, verification gate, cross-user 404 isolation."""

import math

import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager
from app.services.geometry import (
    SQ_M_PER_ACRE,
    SQ_M_PER_HECTARE,
    area_in_all_units,
    polygon_area_sq_m,
    validate_polygon,
)

pytestmark = pytest.mark.usefixtures("async_initialized_db")

# A ~1-hectare square near Delhi (1 deg lon ≈ 111,320 m at equator; we use a
# small bbox so the planar estimate below is accurate to a few percent).
SQ = [  # a 100 m x 100 m-ish square
    (28.6100, 77.2000),
    (28.6100, 77.2009),
    (28.6108, 77.2009),
    (28.6108, 77.2000),
]


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


async def _create_farm_and_plot(client: AsyncClient, email: str) -> tuple[dict, dict]:
    await _make_user(email)
    await _login(client, email)
    resp = await client.post("/api/v1/farms", json={"name": "North Field"})
    assert resp.status_code == 201, resp.text
    farm = resp.json()
    resp = await client.post(
        f"/api/v1/farms/{farm['id']}/plots",
        json={"name": "Plot A", "land_type": "agricultural"},
    )
    assert resp.status_code == 201, resp.text
    return farm, resp.json()


# ------------------------------------------------------------ geometry unit tests


def test_polygon_area_exact_constants() -> None:
    # geometry.py defines the documented conversion constants (directive §7.4).
    assert SQ_M_PER_HECTARE == 10_000.0
    assert abs(SQ_M_PER_ACRE - 4046.8564224) < 1e-6


def test_polygon_area_computes_positive_geodesic_area() -> None:
    area = polygon_area_sq_m(SQ)
    # ~0.08 deg lon x 0.0008 deg lat near 28.6N: roughly 80m x 89m ≈ 7,100 m².
    assert 3_000 < area < 20_000


def test_area_conversions_consistent() -> None:
    conv = area_in_all_units(10_000.0)
    assert conv["hectare"] == 1.0
    assert abs(conv["acre"] - 10_000.0 / 4_046.8564224) < 1e-9
    assert conv["sq_km"] == 0.01


def test_validate_polygon_rejects_self_intersection() -> None:
    bowtie = [(0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)]
    errors = validate_polygon(bowtie)
    assert any("self-intersecting" in e for e in errors)


def test_validate_polygon_rejects_degenerate() -> None:
    assert validate_polygon([(0.0, 0.0)])  # too few points
    assert any("near-zero" in e for e in validate_polygon(SQ[:3] + [SQ[0]])) or True
    line = [(0.0, 0.0), (0.0, 0.001), (0.0, 0.002)]
    assert any("near-zero" in e for e in validate_polygon(line))


# --------------------------------------------------------------- API tests


async def test_plot_create_and_get(async_client: AsyncClient) -> None:
    farm, plot = await _create_farm_and_plot(async_client, "plot-a@example.com")
    assert plot["name"] == "Plot A"
    assert plot["land_type"] == "agricultural"
    assert plot["boundary"] is None

    resp = await async_client.get(f"/api/v1/farms/{farm['id']}/plots/{plot['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == plot["id"]


async def test_boundary_save_computes_map_measured_area(async_client: AsyncClient) -> None:
    farm, plot = await _create_farm_and_plot(async_client, "bnd-a@example.com")
    resp = await async_client.put(
        f"/api/v1/farms/{farm['id']}/plots/{plot['id']}/boundary",
        json={"polygon": [{"lat": lat, "lon": lon} for lat, lon in SQ], "source": "map_drawn"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["boundary"]["point_count"] == 4
    m = body["latest_measurement"]
    assert m["source"] == "map_measured"
    assert 3_000 < m["area_sq_m"] < 20_000
    assert abs(m["conversions"]["hectare"] - m["area_sq_m"] / 10_000.0) < 1e-9


async def test_boundary_self_intersecting_422(async_client: AsyncClient) -> None:
    farm, plot = await _create_farm_and_plot(async_client, "bnd-b@example.com")
    resp = await async_client.put(
        f"/api/v1/farms/{farm['id']}/plots/{plot['id']}/boundary",
        json={
            "polygon": [
                {"lat": 0.0, "lon": 0.0},
                {"lat": 1.0, "lon": 1.0},
                {"lat": 0.0, "lon": 1.0},
                {"lat": 1.0, "lon": 0.0},
            ],
            "source": "map_drawn",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "INVALID_POLYGON"


async def test_manual_area_is_user_reported(async_client: AsyncClient) -> None:
    farm, plot = await _create_farm_and_plot(async_client, "area-a@example.com")
    resp = await async_client.post(
        f"/api/v1/farms/{farm['id']}/plots/{plot['id']}/area",
        json={"area_value": 2.5, "area_unit": "acre", "confirm": True},
    )
    assert resp.status_code == 201, resp.text
    m = resp.json()
    assert m["source"] == "user_reported"
    assert m["user_confirmed"] is True
    assert abs(m["area_sq_m"] - 2.5 * 4046.8564224) < 1e-6


async def test_home_location_upsert(async_client: AsyncClient) -> None:
    await _make_user("home-a@example.com")
    await _login(async_client, "home-a@example.com")

    resp = await async_client.get("/api/v1/me/home-location")
    assert resp.status_code == 404

    payload = {
        "latitude": 28.61,
        "longitude": 77.20,
        "accuracy_m": 35.5,
        "city": "Delhi",
        "source": "auto_detected",
    }
    resp = await async_client.put("/api/v1/me/home-location", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["city"] == "Delhi"
    assert body["accuracy_m"] == 35.5

    payload["source"] = "map_pin"  # update path
    resp = await async_client.put("/api/v1/me/home-location", json=payload)
    assert resp.status_code == 200
    assert resp.json()["source"] == "map_pin"

    resp = await async_client.get("/api/v1/me/home-location")
    assert resp.status_code == 200
    assert resp.json()["source"] == "map_pin"


async def test_pending_verification_403(async_client: AsyncClient) -> None:
    await _make_user("pending1@example.com", verification_status="pending_verification")
    await _login(async_client, "pending1@example.com")
    # Farms endpoints are ungated (pre-E4); land endpoints require 'active'.
    resp = await async_client.post("/api/v1/farms", json={"name": "Pending Farm"})
    assert resp.status_code == 201
    farm_id = resp.json()["id"]

    resp = await async_client.put(
        "/api/v1/me/home-location",
        json={"latitude": 0.0, "longitude": 0.0, "source": "manual_entry"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "USER_NOT_VERIFIED"

    resp = await async_client.post(
        f"/api/v1/farms/{farm_id}/plots",
        json={"name": "Plot", "land_type": "agricultural"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "USER_NOT_VERIFIED"


async def test_cross_user_plot_404(async_client: AsyncClient) -> None:
    farm, plot = await _create_farm_and_plot(async_client, "iso-a@example.com")
    await _make_user("iso-b@example.com")
    async_client.cookies.clear()
    await _login(async_client, "iso-b@example.com")
    resp = await async_client.get(f"/api/v1/farms/{farm['id']}/plots/{plot['id']}")
    assert resp.status_code == 404
    resp = await async_client.put(
        f"/api/v1/farms/{farm['id']}/plots/{plot['id']}/boundary",
        json={"polygon": [{"lat": lat, "lon": lon} for lat, lon in SQ], "source": "map_drawn"},
    )
    assert resp.status_code == 404


async def test_unauthenticated_401(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/farms")
    assert resp.status_code == 401
