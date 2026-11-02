"""Audit event model for security-sensitive actions."""

import uuid
from datetime import UTC, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class AuditEventType(str, PyEnum):
    """Types of audit events."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_VERIFIED = "email_verified"

    # Session
    SESSION_CREATED = "session_created"
    SESSION_REVOKED = "session_revoked"
    SESSION_EXPIRED = "session_expired"
    REFRESH_TOKEN_ROTATED = "refresh_token_rotated"
    REFRESH_TOKEN_REVOKED = "refresh_token_revoked"

    # Account
    ACCOUNT_CREATED = "account_created"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    ACCOUNT_REACTIVATED = "account_reactivated"
    ROLE_CHANGED = "role_changed"

    # Farm
    FARM_CREATED = "farm_created"
    FARM_UPDATED = "farm_updated"
    FARM_DELETED = "farm_deleted"
    FARM_MEMBER_ADDED = "farm_member_added"
    FARM_MEMBER_REMOVED = "farm_member_removed"
    FARM_MEMBER_ROLE_CHANGED = "farm_member_role_changed"

    # Conversation
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_ARCHIVED = "conversation_archived"
    MESSAGE_SENT = "message_sent"

    # Research
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    RESEARCH_FAILED = "research_failed"

    # Security
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_EXPORT_REQUESTED = "data_export_requested"
    DATA_DELETION_REQUESTED = "data_deletion_requested"


class AuditEvent(Base, UUIDMixin):
    """Audit event for security-sensitive actions."""

    __tablename__ = "audit_events"

    # Actor (who performed the action)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )  # user, system, admin

    # Action
    event_type: Mapped[AuditEventType] = mapped_column(
        SQLEnum(AuditEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    event_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # auth, session, account, farm, conversation, research, security

    # Subject (what was acted upon)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    subject_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # user, farm, conversation, etc.

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Result
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    actor: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_events",
        foreign_keys="AuditEvent.actor_id",
    )

    __table_args__ = (
        Index("ix_audit_events_actor_occurred", "actor_id", "occurred_at"),
        Index("ix_audit_events_type_occurred", "event_type", "occurred_at"),
        Index("ix_audit_events_subject", "subject_type", "subject_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditEvent(id={self.id}, type={self.event_type}, actor={self.actor_id}, success={self.success})>"


# Need to import func and uuid
import uuid  # noqa: E402

from sqlalchemy import func  # noqa: E402
