"""Feedback model for synthetic-safe tester input (E1).

Stores brief, non-sensitive feedback submitted by testers via the public
endpoint. Per master prompt §7: never collect passwords, OTPs, private farm
data or unnecessary personal information in feedback reports.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, UUIDMixin


class Feedback(Base, TimestampMixin, UUIDMixin):
    """Minimal tester feedback: category, message, email, app version.

    Email is collected only so the owner can reply. No passwords, OTPs,
    farm data, or unnecessary identifiers.
    """

    __tablename__ = "feedback"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
