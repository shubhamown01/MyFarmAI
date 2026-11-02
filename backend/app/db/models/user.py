"""User and authentication models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.audit import AuditEvent
    from app.db.models.conversation import Conversation
    from app.db.models.farm import Farm, FarmMember
    from app.db.models.session import RefreshToken, Session


class UserRole(str, Enum):
    """User roles in the system."""

    USER = "user"
    ADMIN = "admin"


class User(Base, TimestampMixin, UUIDMixin):
    """User account model."""

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # E3 verification lifecycle: active (admin-created / no selfie flow),
    # pending_verification (fresh self-signup), rejected. Wave 1 only
    # transitions active -> pending_verification at signup activation.
    verification_status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, server_default="active"
    )

    # Relationships
    owned_farms: Mapped[list["Farm"]] = relationship(
        "Farm",
        back_populates="owner",
        foreign_keys="Farm.owner_id",
        cascade="all, delete-orphan",
    )
    farm_memberships: Mapped[list["FarmMember"]] = relationship(
        "FarmMember",
        back_populates="user",
        foreign_keys="FarmMember.user_id",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="actor",
        foreign_keys="AuditEvent.actor_id",
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
