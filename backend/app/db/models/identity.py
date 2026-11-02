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

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
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
