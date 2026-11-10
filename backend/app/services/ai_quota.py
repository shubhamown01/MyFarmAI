"""§10 cloud-AI quota service (C-Q01).

Enforces the master-directive §10 rule (implementing
docs/deployment/CLOUD_COST_AND_QUOTA_POLICY.md §3.1): at most
``limit`` cloud-AI queries per user per aligned UTC window. The counter is
a single atomic ``INSERT ... ON CONFLICT (user_id, window_start)
DO UPDATE ... WHERE used_count < limit`` — the affected-rowcount decides
admission, so concurrent requests can never exceed the limit (no
read-then-increment race). Works on PostgreSQL and SQLite (both support
the upsert with a conditional WHERE).

Wire-time limitation (disclosed): the slot is consumed just before the
generation call, so it counts INTENT, not confirmed success. §10 says
"successful queries" — true success-only accounting (decrement on
generation failure) will be added when the cloud-LLM provider itself is
wired; the flag is off until then, so nothing counts today.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models.ai_quota import AiQuotaCounter


def window_start_for(now: datetime, window_hours: int) -> datetime:
    """Start of the aligned UTC window containing ``now`` (stable bucket)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    epoch = 3600 * window_hours
    ts = int(now.timestamp()) // epoch * epoch
    return datetime.fromtimestamp(ts, tz=UTC)


def _statement(dialect_name: str, user_id: uuid.UUID, window_start: datetime, limit: int):
    col = AiQuotaCounter.__table__.c
    ins = pg_insert if dialect_name == "postgresql" else sqlite_insert
    return (
        ins(AiQuotaCounter)
        .values(user_id=user_id, window_start=window_start, used_count=1)
        .on_conflict_do_update(
            index_elements=["user_id", "window_start"],
            set_={"used_count": col.used_count + 1},
            where=col.used_count < limit,
        )
    )


def consume_slot(session: Session, user_id: uuid.UUID, *, limit: int, window_hours: int) -> bool:
    """Atomically consume one cloud-AI slot for ``user_id``. True = admitted."""
    ws = window_start_for(datetime.now(UTC), window_hours)
    result = session.execute(_statement(session.connection().dialect.name, user_id, ws, limit))
    session.commit()
    return (result.rowcount or 0) > 0


async def aconsume_slot(
    session: AsyncSession, user_id: uuid.UUID, *, limit: int, window_hours: int
) -> bool:
    """Async variant of :func:`consume_slot` (commit handled by caller's transaction)."""
    ws = window_start_for(datetime.now(UTC), window_hours)
    conn = await session.connection()
    result = await session.execute(_statement(conn.dialect.name, user_id, ws, limit))
    return (result.rowcount or 0) > 0


def remaining(session: Session, user_id: uuid.UUID, *, limit: int, window_hours: int) -> int:
    """Advisory read: slots left for ``user_id`` in the current window."""
    ws = window_start_for(datetime.now(UTC), window_hours)
    used: int | None = session.scalars(
        select(AiQuotaCounter.used_count).where(
            AiQuotaCounter.user_id == user_id, AiQuotaCounter.window_start == ws
        )
    ).first()
    return max(0, limit - (used or 0))


async def ausage_rows(
    session: AsyncSession, *, limit: int, window_hours: int
) -> list[dict[str, object]]:
    """Admin view: per-user usage in the current window (§4 dashboard data)."""
    ws = window_start_for(datetime.now(UTC), window_hours)
    rows = await session.execute(
        select(AiQuotaCounter.user_id, AiQuotaCounter.used_count)
        .where(AiQuotaCounter.window_start == ws)
        .order_by(AiQuotaCounter.used_count.desc())
    )
    return [
        {"user_id": str(uid), "used": used, "limit": limit, "remaining": max(0, limit - used)}
        for uid, used in rows.all()
    ]
