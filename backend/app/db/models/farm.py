"""Farm and farm membership models."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.crop import CropCycle
    from app.db.models.conversation import Conversation


class FarmRole(str, PyEnum):
    """Farm membership roles."""

    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Farm(Base, TimestampMixin, UUIDMixin):
    """Farm model representing a physical farm location."""

    __tablename__ = "farms"

    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )

    # Ownership
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Settings
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_farms",
        foreign_keys="Farm.owner_id",
    )
    members: Mapped[list["FarmMember"]] = relationship(
        "FarmMember",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    crop_cycles: Mapped[list["CropCycle"]] = relationship(
        "CropCycle",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="farm",
        foreign_keys="Conversation.farm_id",
    )

    # Indexes and constraints
    __table_args__ = (
        Index("ix_farms_owner_active", "owner_id", "is_active"),
        Index("ix_farms_location", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Farm(id={self.id}, name={self.name}, owner_id={self.owner_id})>"


class FarmMember(Base, TimestampMixin, UUIDMixin):
    """Farm membership linking users to farms with roles."""

    __tablename__ = "farm_members"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[FarmRole] = mapped_column(
        SQLEnum(FarmRole, native_enum=False),
        default=FarmRole.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    farm: Mapped["Farm"] = relationship(
        "Farm",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="farm_memberships",
        foreign_keys="FarmMember.user_id",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("farm_id", "user_id", name="uq_farm_member"),
        Index("ix_farm_members_farm_role", "farm_id", "role"),
    )

    def __repr__(self) -> str:
        return f"<FarmMember(farm_id={self.farm_id}, user_id={self.user_id}, role={self.role})>"