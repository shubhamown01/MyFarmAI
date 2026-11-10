"""Farmer profile + onboarding service (E5).

Onboarding state is COMPUTED from existing records (user, verification,
home location, farms/plots, profile) — no separate state table, so the
displayed state can never drift from the source of truth.

Step order (directive §4.2): contact_verified → verification (selfie
review) → location → land → profile.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.farm import Farm, FarmMember
from app.db.models.land import FarmPlot, HomeLocation
from app.db.models.profile import FarmerProfile
from app.db.models.user import User

# Order matters — defines next_step.
ONBOARDING_STEPS = ("contact_verified", "verification", "location", "land", "profile")


class ProfileNotFoundError(Exception):
    pass


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -------------------------------------------------------------- profile

    async def get_profile(self, user_id: str) -> FarmerProfile | None:
        stmt = select(FarmerProfile).where(FarmerProfile.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def save_profile(self, user_id: str, **kwargs: object) -> FarmerProfile:
        """Upsert. profile_completed flips in code (never client-supplied)."""
        profile = await self.get_profile(user_id)
        if profile is None:
            profile = FarmerProfile(user_id=user_id, **kwargs)
            self._session.add(profile)
        else:
            for key, value in kwargs.items():
                setattr(profile, key, value)
        await self._session.flush()
        profile.profile_completed = bool(profile.full_name and profile.farming_type)
        await self._session.flush()
        return profile

    # ----------------------------------------------------------- onboarding

    async def onboarding_status(self, user_id: str) -> dict[str, object]:
        user = await self._session.get(User, uuid.UUID(user_id))
        if user is None:
            raise ProfileNotFoundError(user_id)

        home = (
            await self._session.execute(
                select(HomeLocation.id).where(HomeLocation.user_id == user_id)
            )
        ).scalar_one_or_none()

        farm_plot = (
            await self._session.execute(
                select(FarmPlot.id)
                .join(Farm, Farm.id == FarmPlot.farm_id)
                .join(FarmMember, FarmMember.farm_id == Farm.id)
                .where(FarmMember.user_id == user_id)
                .limit(1)
            )
        ).scalar_one_or_none()

        profile = await self.get_profile(user_id)

        steps: list[dict[str, object]] = [
            {
                "step": "contact_verified",
                "complete": bool(user.email_verified),
                "detail": None
                if user.email_verified
                else "verify your email or sign in with a provider",
            },
            {
                "step": "verification",
                "complete": user.verification_status in ("active", "verified"),
                "detail": f"verification_status={user.verification_status}",
            },
            {"step": "location", "complete": home is not None, "detail": None},
            {"step": "land", "complete": farm_plot is not None, "detail": None},
            {
                "step": "profile",
                "complete": bool(profile and profile.profile_completed),
                "detail": None,
            },
        ]
        next_step = next((str(s["step"]) for s in steps if not s["complete"]), None)
        return {
            "verification_status": user.verification_status,
            "steps": steps,
            "next_step": next_step,
            "complete": next_step is None,
        }
