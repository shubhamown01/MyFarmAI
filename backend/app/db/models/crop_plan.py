"""Crop planning models (P7B): farmer-controlled plans, tasks, revision history.

Owner-approved schema (FCL-080). Farmer decisions are never silently
overwritten: user tasks are only ever edited by the user (soft-cancel, no
hard delete), and every plan mutation appends an immutable revision record.
Milestone derivation lives in the service layer — it uses ONLY existing
Crop.growing_days_min/max and displays its assumptions verbatim.
"""

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.farm import Farm
    from app.db.models.user import User


class CropPlanTaskSource(str, PyEnum):
    """Who created a plan task. User tasks are never system-modified."""

    USER = "user"
    SUGGESTED = "suggested"


class CropPlanTaskStatus(str, PyEnum):
    """Task lifecycle. 'cancelled' is a soft delete — history is preserved."""

    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class CropPlan(Base, TimestampMixin, UUIDMixin):
    """A farmer's crop plan attached to a farm (optionally to a cycle)."""

    __tablename__ = "crop_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_cycle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crop_cycles.id", ondelete="SET NULL"),
        nullable=True,
    )
    variety: Mapped[str | None] = mapped_column(String(100), nullable=True)
    planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)

    if TYPE_CHECKING:
        from app.db.models.crop import CropCycle

        cycle: CropCycle | None

    tasks: Mapped[list["CropPlanTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )
    revisions: Mapped[list["CropPlanRevision"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class CropPlanTask(Base, TimestampMixin, UUIDMixin):
    """A task on a plan. Suggested tasks come from derivations; user tasks
    are the farmer's own decisions (freely editable, never auto-modified)."""

    __tablename__ = "crop_plan_tasks"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crop_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[CropPlanTaskSource] = mapped_column(
        SQLEnum(CropPlanTaskSource, native_enum=False),
        default=CropPlanTaskSource.USER,
        nullable=False,
    )
    status: Mapped[CropPlanTaskStatus] = mapped_column(
        SQLEnum(CropPlanTaskStatus, native_enum=False),
        default=CropPlanTaskStatus.PENDING,
        nullable=False,
    )

    plan: Mapped["CropPlan"] = relationship(back_populates="tasks")


class CropPlanRevision(Base, UUIDMixin):
    """Append-only plan-change history: who changed what, with a snapshot
    of the plan (and its tasks) before the change. Never updated or deleted."""

    __tablename__ = "crop_plan_revisions"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crop_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped["CropPlan"] = relationship(back_populates="revisions")
