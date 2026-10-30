"""Farm context service tests (P5A-03/P5A-04): authorized context, unknown fields."""

import pytest

from app.core.security import hash_password
from app.db.models.user import User
from app.db.repositories import CropRepository, FarmRepository
from app.db.session import db_manager
from app.services.context import FarmContextService
from app.services.farm import FarmNotFoundError, FarmService

pytestmark = pytest.mark.usefixtures("async_initialized_db")


async def _make_user(email: str) -> User:
    async with db_manager.session() as session:
        user = User(email=email, password_hash=hash_password("Pass-2026!x"))
        session.add(user)
        return user


async def _setup_full_farm(user: User) -> str:
    """Farm with address + coordinates and one active + one harvested cycle."""
    async with db_manager.session() as session:
        farms = FarmRepository(session)
        crops = CropRepository(session)
        farm = await farms.create(owner_id=str(user.id), name="Context Farm")
        farm.address = "Village X"
        farm.latitude, farm.longitude = 28.61, 77.20
        tomato = await crops.create(name="Tomato")
        wheat = await crops.create(name="Wheat")
        from app.db.repositories import CropCycleRepository

        cycles = CropCycleRepository(session)
        await cycles.create(
            farm_id=str(farm.id), crop_id=str(tomato.id), season_year=2026, status="planted"
        )
        await cycles.create(
            farm_id=str(farm.id), crop_id=str(wheat.id), season_year=2025, status="harvested"
        )
        return str(farm.id)


async def test_member_gets_full_context():
    user = await _make_user("ctx1@example.com")
    farm_id = await _setup_full_farm(user)
    async with db_manager.session() as session:
        svc = FarmContextService(session, FarmService(session))
        ctx = await svc.get_context(str(user.id), farm_id)
    assert ctx.name == "Context Farm"
    assert ctx.latitude == 28.61 and ctx.longitude == 77.20
    assert ctx.active_crops == ["Tomato"]  # harvested wheat excluded


async def test_unknown_fields_stay_unknown():
    user = await _make_user("ctx2@example.com")
    async with db_manager.session() as session:
        farm = await FarmRepository(session).create(owner_id=str(user.id), name="Bare Farm")
        farm_id = str(farm.id)
    async with db_manager.session() as session:
        svc = FarmContextService(session, FarmService(session))
        ctx = await svc.get_context(str(user.id), farm_id)
    assert ctx.address is None
    assert ctx.latitude is None and ctx.longitude is None
    assert ctx.active_crops == []  # unknown, never fabricated


async def test_non_member_404():
    user = await _make_user("ctx3@example.com")
    outsider = await _make_user("ctx4@example.com")
    farm_id = await _setup_full_farm(user)
    async with db_manager.session() as session:
        svc = FarmContextService(session, FarmService(session))
        with pytest.raises(FarmNotFoundError):
            await svc.get_context(str(outsider.id), farm_id)
