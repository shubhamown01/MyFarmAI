"""§10 cloud-AI quota counter (C-Q01).

One row per (user, quota window); ``used_count`` is incremented by a single
atomic ``INSERT ... ON CONFLICT ... DO UPDATE ... WHERE`` so concurrent
requests cannot exceed the configured limit (Cloud
CLOUD_COST_AND_QUOTA_POLICY.md §3.1). Inactive until ``cloud_ai_enabled``.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import GUID, Base


class AiQuotaCounter(Base):
    """Cloud-AI query count for one user in one aligned quota window."""

    __tablename__ = "ai_quota_counters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Start of the aligned UTC window (e.g. 10h buckets). Aware UTC datetimes.
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "window_start"),)
