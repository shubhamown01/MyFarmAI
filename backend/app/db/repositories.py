"""SQLAlchemy repositories for database operations."""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AuditEvent,
    Citation,
    Conversation,
    Crop,
    CropCycle,
    Farm,
    FarmMember,
    Message,
    RefreshToken,
    ResearchQuery,
    ResearchSource,
    User,
)
from app.db.models import (
    Session as SessionModel,
)
from app.db.models.conversation import MessageRole
from app.db.models.crop import CropCategory, CropCycleStatus
from app.db.models.farm import FarmRole

if TYPE_CHECKING:
    pass


class UserRepository:
    """Repository for user operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        preferred_language: str = "en",
        timezone: str = "UTC",
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            preferred_language=preferred_language,
            timezone=timezone,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_session_id_hash(self, session_id_hash: str) -> User | None:
        from app.db.models.session import Session as SessionModel

        result = await self.session.execute(
            select(User)
            .join(SessionModel, SessionModel.user_id == User.id)
            .where(SessionModel.session_id_hash == session_id_hash)
            .where(SessionModel.is_revoked.is_(False))
            .where(SessionModel.expires_at > func.now())
        )
        return result.scalar_one_or_none()

    async def update_last_login(self, user_id: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(last_login_at=func.now())
        )

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(password_hash=password_hash)
        )

    async def deactivate(self, user_id: str) -> None:
        await self.session.execute(update(User).where(User.id == user_id).values(is_active=False))

    async def delete(self, user_id: str) -> None:
        await self.session.execute(delete(User).where(User.id == user_id))


class FarmRepository:
    """Repository for farm operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        owner_id: str,
        name: str,
        description: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        timezone: str = "UTC",
    ) -> Farm:
        farm = Farm(
            owner_id=owner_id,
            name=name,
            description=description,
            address=address,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        self.session.add(farm)
        await self.session.flush()
        # Add owner as farm member
        member = FarmMember(
            farm_id=farm.id,
            user_id=owner_id,
            role=FarmRole.OWNER,
        )
        self.session.add(member)
        await self.session.flush()
        return farm

    async def get_by_id(self, farm_id: str) -> Farm | None:
        result = await self.session.execute(select(Farm).where(Farm.id == farm_id))
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: str) -> Sequence[Farm]:
        result = await self.session.execute(
            select(Farm)
            .where(Farm.owner_id == owner_id)
            .where(Farm.is_active.is_(True))
            .order_by(Farm.created_at.desc())
        )
        return result.scalars().all()

    async def get_user_farms(self, user_id: str) -> Sequence[Farm]:
        result = await self.session.execute(
            select(Farm)
            .join(FarmMember, FarmMember.farm_id == Farm.id)
            .where(FarmMember.user_id == user_id)
            .where(Farm.is_active.is_(True))
            .order_by(Farm.created_at.desc())
        )
        return result.scalars().all()

    async def update(
        self,
        farm_id: str,
        name: str | None = None,
        description: str | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        timezone: str | None = None,
        is_active: bool | None = None,
    ) -> Farm | None:
        farm = await self.get_by_id(farm_id)
        if not farm:
            return None
        if name is not None:
            farm.name = name
        if description is not None:
            farm.description = description
        if address is not None:
            farm.address = address
        if latitude is not None:
            farm.latitude = latitude
        if longitude is not None:
            farm.longitude = longitude
        if timezone is not None:
            farm.timezone = timezone
        if is_active is not None:
            farm.is_active = is_active
        await self.session.flush()
        return farm

    async def add_member(
        self,
        farm_id: str,
        user_id: str,
        role: FarmRole = FarmRole.MEMBER,
        invited_by: str | None = None,
    ) -> FarmMember:
        member = FarmMember(
            farm_id=farm_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def remove_member(self, farm_id: str, user_id: str) -> bool:
        result = await self.session.execute(
            delete(FarmMember).where(
                FarmMember.farm_id == farm_id,
                FarmMember.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def update_member_role(
        self,
        farm_id: str,
        user_id: str,
        role: FarmRole,
    ) -> FarmMember | None:
        result = await self.session.execute(
            select(FarmMember).where(
                FarmMember.farm_id == farm_id,
                FarmMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return None
        member.role = role
        await self.session.flush()
        return member

    async def get_member(self, farm_id: str, user_id: str) -> FarmMember | None:
        result = await self.session.execute(
            select(FarmMember).where(
                FarmMember.farm_id == farm_id,
                FarmMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_members(self, farm_id: str) -> Sequence[FarmMember]:
        result = await self.session.execute(select(FarmMember).where(FarmMember.farm_id == farm_id))
        return result.scalars().all()


class CropRepository:
    """Repository for crop catalogue operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        scientific_name: str | None = None,
        category: CropCategory = CropCategory.OTHER,
        description: str | None = None,
        min_temp_c: float | None = None,
        max_temp_c: float | None = None,
        optimal_rainfall_mm: float | None = None,
        growing_days_min: int | None = None,
        growing_days_max: int | None = None,
    ) -> Crop:
        crop = Crop(
            name=name,
            scientific_name=scientific_name,
            category=category,
            description=description,
            min_temp_c=min_temp_c,
            max_temp_c=max_temp_c,
            optimal_rainfall_mm=optimal_rainfall_mm,
            growing_days_min=growing_days_min,
            growing_days_max=growing_days_max,
        )
        self.session.add(crop)
        await self.session.flush()
        return crop

    async def get_by_id(self, crop_id: str) -> Crop | None:
        result = await self.session.execute(select(Crop).where(Crop.id == crop_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Crop | None:
        result = await self.session.execute(select(Crop).where(Crop.name == name))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        category: CropCategory | None = None,
        is_active: bool = True,
    ) -> Sequence[Crop]:
        query = select(Crop).where(Crop.is_active == is_active)
        if category:
            query = query.where(Crop.category == category)
        query = query.order_by(Crop.name)
        result = await self.session.execute(query)
        return result.scalars().all()


class CropCycleRepository:
    """Repository for crop cycle operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        farm_id: str,
        crop_id: str,
        season_year: int,
        season_name: str | None = None,
        planting_date: datetime | None = None,
        expected_harvest_date: datetime | None = None,
        area_hectares: float | None = None,
        area_acres: float | None = None,
        status: CropCycleStatus = CropCycleStatus.PLANNED,
        expected_yield_kg: float | None = None,
        yield_unit: str = "kg/ha",
        notes: str | None = None,
    ) -> CropCycle:
        cycle = CropCycle(
            farm_id=farm_id,
            crop_id=crop_id,
            season_year=season_year,
            season_name=season_name,
            planting_date=planting_date,
            expected_harvest_date=expected_harvest_date,
            area_hectares=area_hectares,
            area_acres=area_acres,
            status=status,
            expected_yield_kg=expected_yield_kg,
            yield_unit=yield_unit,
            notes=notes,
        )
        self.session.add(cycle)
        await self.session.flush()
        return cycle

    async def get_by_id(self, cycle_id: str) -> CropCycle | None:
        result = await self.session.execute(select(CropCycle).where(CropCycle.id == cycle_id))
        return result.scalar_one_or_none()

    async def list_by_farm(
        self,
        farm_id: str,
        status: CropCycleStatus | None = None,
    ) -> Sequence[CropCycle]:
        query = select(CropCycle).where(CropCycle.farm_id == farm_id)
        if status:
            query = query.where(CropCycle.status == status)
        query = query.order_by(CropCycle.season_year.desc(), CropCycle.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()


class ConversationRepository:
    """Repository for conversation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        language: str = "en",
        crop: str | None = None,
        location: str | None = None,
        farm_id: uuid.UUID | None = None,
        model_name: str | None = None,
        model_version: str | None = None,
    ) -> Conversation:
        conversation = Conversation(
            user_id=user_id,
            farm_id=farm_id,
            language=language,
            crop=crop,
            location=location,
            model_name=model_name,
            model_version=model_version,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        """Ownership-scoped fetch (deny-by-default; cross-user looks like not-found)."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_messages(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation and conversation.messages:
            # Sort messages by created_at
            conversation.messages = sorted(
                conversation.messages,
                key=lambda m: m.created_at,
            )[-limit:]
        return conversation

    async def get_user_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        farm_id: uuid.UUID | None = None,
    ) -> Sequence[Conversation]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_archived.is_(False))
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        if farm_id:
            query = query.where(Conversation.farm_id == farm_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_context(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        language: str | None = None,
        crop: str | None = None,
        location: str | None = None,
        model_name: str | None = None,
        model_version: str | None = None,
    ) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            return None
        if language is not None:
            conversation.language = language
        if crop is not None:
            conversation.crop = crop
        if location is not None:
            conversation.location = location
        if model_name is not None:
            conversation.model_name = model_name
        if model_version is not None:
            conversation.model_version = model_version
        await self.session.flush()
        return conversation

    async def increment_message_count(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
            .values(message_count=Conversation.message_count + 1)
        )

    async def archive(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
            .values(is_archived=True)
        )
        return result.rowcount > 0

    async def delete(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        )
        return result.rowcount > 0


class MessageRepository:
    """Repository for message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        model_name: str | None = None,
        model_version: str | None = None,
        token_count: int | None = None,
        finish_reason: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model_name=model_name,
            model_version=model_version,
            token_count=token_count,
            finish_reason=finish_reason,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_recent(
        self,
        conversation_id: uuid.UUID,
        limit: int = 10,
    ) -> Sequence[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))

    async def count(self, conversation_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        return result.scalar_one()


class ResearchRepository:
    """Repository for research operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_query(
        self,
        user_id: str,
        query_text: str,
        language: str = "en",
    ) -> ResearchQuery:
        query = ResearchQuery(
            user_id=user_id,
            query_text=query_text,
            language=language,
        )
        self.session.add(query)
        await self.session.flush()
        return query

    async def get_query(self, query_id: str) -> ResearchQuery | None:
        result = await self.session.execute(
            select(ResearchQuery).where(ResearchQuery.id == query_id)
        )
        return result.scalar_one_or_none()

    async def update_query_status(
        self,
        query_id: str,
        status: str,
        answer: str | None = None,
        confidence_score: float | None = None,
        model_name: str | None = None,
        model_version: str | None = None,
        token_count: int | None = None,
        error_message: str | None = None,
    ) -> ResearchQuery | None:
        from app.db.models.research import ResearchQueryStatus

        result = await self.session.execute(
            select(ResearchQuery).where(ResearchQuery.id == query_id)
        )
        query = result.scalar_one_or_none()
        if not query:
            return None
        query.status = ResearchQueryStatus(status)
        if answer is not None:
            query.answer = answer
        if confidence_score is not None:
            query.confidence_score = confidence_score
        if model_name is not None:
            query.model_name = model_name
        if model_version is not None:
            query.model_version = model_version
        if token_count is not None:
            query.token_count = token_count
        if error_message is not None:
            query.error_message = error_message
        if status in ("completed", "failed"):
            query.completed_at = func.now()
        await self.session.flush()
        return query

    async def add_source(
        self,
        query_id: str,
        url: str,
        title: str | None = None,
        domain: str | None = None,
        publisher: str | None = None,
        published_at: datetime | None = None,
        content_text: str | None = None,
        content_hash: str | None = None,
    ) -> ResearchSource:
        source = ResearchSource(
            query_id=query_id,
            url=url,
            title=title,
            domain=domain,
            publisher=publisher,
            published_at=published_at,
            content_text=content_text,
            content_hash=content_hash,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def add_citation(
        self,
        query_id: str,
        source_id: str,
        claim_text: str,
        source_excerpt: str,
        position_in_answer: int | None = None,
    ) -> Citation:
        citation = Citation(
            query_id=query_id,
            source_id=source_id,
            claim_text=claim_text,
            source_excerpt=source_excerpt,
            position_in_answer=position_in_answer,
        )
        self.session.add(citation)
        await self.session.flush()
        return citation


class SessionRepository:
    """Repository for session operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        session_id_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_info: str | None = None,
    ) -> SessionModel:
        session_obj = SessionModel(
            user_id=user_id,
            session_id_hash=session_id_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
        )
        self.session.add(session_obj)
        await self.session.flush()
        return session_obj

    async def get_by_hash(self, session_id_hash: str) -> SessionModel | None:
        result = await self.session.execute(
            select(SessionModel).where(SessionModel.session_id_hash == session_id_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, session_id_hash: str, reason: str | None = None) -> bool:
        result = await self.session.execute(
            update(SessionModel)
            .where(SessionModel.session_id_hash == session_id_hash)
            .where(SessionModel.is_revoked.is_(False))
            .values(
                is_revoked=True,
                revoked_at=func.now(),
                revoked_reason=reason,
            )
        )
        return result.rowcount > 0

    async def revoke_all_user_sessions(self, user_id: str, reason: str | None = None) -> int:
        result = await self.session.execute(
            update(SessionModel)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.is_revoked.is_(False))
            .values(
                is_revoked=True,
                revoked_at=func.now(),
                revoked_reason=reason,
            )
        )
        return result.rowcount

    async def cleanup_expired(self) -> int:
        result = await self.session.execute(
            delete(SessionModel).where(SessionModel.expires_at < func.now())
        )
        return result.rowcount


class RefreshTokenRepository:
    """Repository for refresh token operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        parent_token_hash: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_info: str | None = None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            parent_token_hash=parent_token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_hash: str, reason: str | None = None) -> bool:
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(
                is_revoked=True,
                revoked_at=func.now(),
                revoked_reason=reason,
            )
        )
        return result.rowcount > 0

    async def revoke_chain(self, token_hash: str, reason: str | None = None) -> int:
        # Revoke this token and all its descendants
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.parent_token_hash == token_hash)
            .values(
                is_revoked=True,
                revoked_at=func.now(),
                revoked_reason=reason,
            )
        )
        # Also revoke the token itself
        await self.revoke(token_hash, reason)
        return result.rowcount + 1

    async def revoke_all_user_tokens(self, user_id: str, reason: str | None = None) -> int:
        """Revoke every live refresh token owned by the user (reuse-detection response).

        Exit-gate fix: chain-walking alone leaves tokens >=2 generations old
        live; suspected theft revokes everything for this user instead.
        """
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)  # noqa: E712
            .values(
                is_revoked=True,
                revoked_at=func.now(),
                revoked_reason=reason,
            )
        )
        return result.rowcount

    async def cleanup_expired(self) -> int:
        result = await self.session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < func.now())
        )
        return result.rowcount


class AuditRepository:
    """Repository for audit event operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        event_type: str,
        event_category: str,
        description: str,
        actor_id: str | None = None,
        actor_type: str = "user",
        subject_id: str | None = None,
        subject_type: str | None = None,
        event_metadata: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_id=actor_id,
            actor_type=actor_type,
            event_type=event_type,
            event_category=event_category,
            subject_id=subject_id,
            subject_type=subject_type,
            description=description,
            event_metadata=event_metadata,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            success=success,
            error_message=error_message,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_user_events(
        self,
        user_id: str,
        limit: int = 50,
    ) -> Sequence[AuditEvent]:
        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.actor_id == user_id)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_events_by_type(
        self,
        event_type: str,
        limit: int = 50,
    ) -> Sequence[AuditEvent]:
        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.event_type == event_type)
            .order_by(AuditEvent.occurred_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
