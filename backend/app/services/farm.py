"""Farm service (P5A-01): thin authorization over FarmRepository.

Authorization model (deny-by-default, ADR-008 404 semantics):
- Non-members get not-found (existence is not leaked).
- VIEWER is read-only; updates require MEMBER or OWNER.
- Member management (add/remove/role change) requires OWNER.

Note: FarmRepository.update() is a raw setter without user scoping; the
service's membership+role check is the required authorization boundary.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditEventType
from app.db.models.farm import Farm, FarmMember, FarmRole
from app.db.repositories import AuditRepository, FarmRepository, UserRepository


class FarmNotFoundError(Exception):
    pass


class FarmPermissionError(Exception):
    pass


class FarmUserNotFoundError(Exception):
    pass


_MEMBER_ROLES = (FarmRole.OWNER, FarmRole.MEMBER)


class FarmService:
    """Farm CRUD and membership with ownership checks."""

    def __init__(self, session: AsyncSession) -> None:
        self._farms = FarmRepository(session)
        self._users = UserRepository(session)
        self._audit = AuditRepository(session)

    async def _audit_log(
        self,
        event_type: AuditEventType,
        description: str,
        actor_id: str,
        subject_id: str,
        subject_type: str,
    ) -> None:
        # ID-only descriptions: farm coordinates/address are never logged (P5A-04).
        await self._audit.log(
            event_type=event_type,
            event_category="farm",
            description=description,
            actor_id=uuid.UUID(actor_id),
            subject_id=uuid.UUID(subject_id),
            subject_type=subject_type,
        )

    async def _authorized_farm(
        self, user_id: str, farm_id: str, *, require: tuple[FarmRole, ...] = _MEMBER_ROLES
    ) -> Farm:
        farm = await self._farms.get_by_id(farm_id)
        if not farm:
            raise FarmNotFoundError(farm_id)
        member = await self._farms.get_member(farm_id, user_id)
        if not member:
            raise FarmNotFoundError(farm_id)
        if member.role not in require:
            raise FarmPermissionError("insufficient farm role")
        return farm

    async def create_farm(self, owner_id: str, **kwargs) -> Farm:
        farm = await self._farms.create(owner_id=owner_id, **kwargs)
        await self._audit_log(
            AuditEventType.FARM_CREATED, "farm created", owner_id, str(farm.id), "farm"
        )
        return farm

    async def list_farms(self, user_id: str) -> list[Farm]:
        return list(await self._farms.get_user_farms(user_id))

    async def get_farm(self, user_id: str, farm_id: str) -> Farm:
        return await self._authorized_farm(
            user_id,
            farm_id,
            require=(
                FarmRole.OWNER,
                FarmRole.MEMBER,
                FarmRole.VIEWER,
            ),
        )

    async def update_farm(self, user_id: str, farm_id: str, **kwargs) -> Farm:
        await self._authorized_farm(user_id, farm_id)
        # Only the owner may (de)activate the farm — members update fields only.
        is_active = kwargs.pop("is_active", None)
        if is_active is not None:
            member = await self._farms.get_member(farm_id, user_id)
            if member is None or member.role != FarmRole.OWNER:
                raise FarmPermissionError("only the farm owner may activate or deactivate the farm")
            kwargs["is_active"] = is_active
        farm = await self._farms.update(farm_id, **kwargs)
        await self._audit_log(AuditEventType.FARM_UPDATED, "farm updated", user_id, farm_id, "farm")
        return farm

    async def list_members(self, user_id: str, farm_id: str) -> list[FarmMember]:
        await self._authorized_farm(
            user_id,
            farm_id,
            require=(
                FarmRole.OWNER,
                FarmRole.MEMBER,
                FarmRole.VIEWER,
            ),
        )
        return list(await self._farms.list_members(farm_id))

    async def add_member(
        self, user_id: str, farm_id: str, new_user_id: str, role: FarmRole
    ) -> FarmMember:
        await self._authorized_farm(user_id, farm_id, require=(FarmRole.OWNER,))
        if not await self._users.get_by_id(new_user_id):
            raise FarmUserNotFoundError(new_user_id)
        if await self._farms.get_member(farm_id, new_user_id):
            raise FarmPermissionError("user is already a member")
        member = await self._farms.add_member(farm_id, new_user_id, role)
        await self._audit_log(
            AuditEventType.FARM_MEMBER_ADDED,
            "farm member added",
            user_id,
            str(new_user_id),
            "user",
        )
        return member

    async def remove_member(self, user_id: str, farm_id: str, target_user_id: str) -> None:
        await self._authorized_farm(user_id, farm_id, require=(FarmRole.OWNER,))
        target = await self._farms.get_member(farm_id, target_user_id)
        if not target:
            raise FarmNotFoundError(target_user_id)
        if target.role == FarmRole.OWNER:
            raise FarmPermissionError("farm owner cannot be removed")
        await self._farms.remove_member(farm_id, target_user_id)
        await self._audit_log(
            AuditEventType.FARM_MEMBER_REMOVED,
            "farm member removed",
            user_id,
            str(target_user_id),
            "user",
        )

    async def update_member_role(
        self, user_id: str, farm_id: str, target_user_id: str, role: FarmRole
    ) -> FarmMember:
        await self._authorized_farm(user_id, farm_id, require=(FarmRole.OWNER,))
        target = await self._farms.get_member(farm_id, target_user_id)
        if not target:
            raise FarmNotFoundError(target_user_id)
        if target.role == FarmRole.OWNER:
            raise FarmPermissionError("farm owner role cannot be changed")
        await self._farms.update_member_role(farm_id, target_user_id, role)
        updated = await self._farms.get_member(farm_id, target_user_id)
        assert updated is not None
        await self._audit_log(
            AuditEventType.FARM_MEMBER_ROLE_CHANGED,
            "farm member role changed",
            user_id,
            str(target_user_id),
            "user",
        )
        return updated
