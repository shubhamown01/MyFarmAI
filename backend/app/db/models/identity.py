"""Identity / verification models (E1 — passwordless email OTP).

``authentication_accounts`` links a user to one or more login providers
(password, email_otp, phone_otp, google, microsoft). Provider values are
stored as plain strings (NOT a DB enum) so adding a provider never requires
a migration.

``contact_verifications`` holds one-time codes pending verification. The
pending User row is created up front (user_id is NOT NULL); single-use
consumption is enforced in code (``consumed_at`` set on success).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import GUID, Base, UUIDMixin


class AuthenticationAccount(Base, UUIDMixin):
    """A user linked to an authentication provider (E1)."""

    __tablename__ = "authentication_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # password | email_otp | phone_otp | google | microsoft — plain string by
    # design: adding a provider must never require a migration.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    # Email address or provider subject identifier.
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "uq_authentication_accounts_provider_account",
            "provider",
            "provider_account_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<AuthenticationAccount(id={self.id}, provider={self.provider})>"


class ContactVerification(Base, UUIDMixin):
    """A one-time verification code for a contact channel (E1)."""

    __tablename__ = "contact_verifications"

    # The pending user row is created up front, so this is never NULL.
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(10), nullable=False)  # email | phone
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    # Single use is enforced in code: set on successful verification.
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_contact_verifications_destination_consumed",
            "destination",
            "consumed_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<ContactVerification(id={self.id}, destination={self.destination})>"


class ConsentRecord(Base, UUIDMixin):
    """A recorded user consent (E3 — e.g. selfie liveness processing)."""

    __tablename__ = "consent_records"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # e.g. selfie_liveness — plain string: adding a consent type never
    # requires a migration.
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    __table_args__ = (Index("ix_consent_records_user_type", "user_id", "consent_type"),)

    def __repr__(self) -> str:
        return f"<ConsentRecord(id={self.id}, consent_type={self.consent_type})>"


class SelfieVerification(Base, UUIDMixin):
    """A liveness selfie upload awaiting manual review (E3 wave 1).

    ``storage_path`` is server-internal — it must NEVER leave the API. Wave 1
    stops at ``pending_review``; the admin queue/review flow is wave 2.
    """

    __tablename__ = "selfie_verifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    challenge_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    vl_hint: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending_review", nullable=False, server_default="pending_review"
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_review', 'approved', 'rejected')",
            name="ck_selfie_verifications_status",
        ),
        Index("ix_selfie_verifications_user_status", "user_id", "status"),
        Index("ix_selfie_verifications_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<SelfieVerification(id={self.id}, status={self.status})>"


class VerificationEvent(Base, UUIDMixin):
    """Audit trail for verification-flow events (E3)."""

    __tablename__ = "verification_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # e.g. CONSENT_GRANTED, CHALLENGE_ISSUED, CAPTURE_UPLOADED — plain string.
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_verification_events_user_created", "user_id", "created_at"),)

    def __repr__(self) -> str:
        return f"<VerificationEvent(id={self.id}, event_type={self.event_type})>"
