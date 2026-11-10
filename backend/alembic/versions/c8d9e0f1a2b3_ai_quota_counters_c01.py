"""ai_quota_counters table for §10 cloud-AI user quota (C-Q01)

Implements the atomic per-user cloud-AI quota counter from
docs/deployment/CLOUD_COST_AND_QUOTA_POLICY.md §3.1 / master directive §10:
natural key (user_id, window_start), one aligned UTC window per row,
used_count incremented atomically so concurrent requests cannot exceed the
limit. Inactive until the cloud_ai_enabled settings flag is turned on.

Revision ID: c8d9e0f1a2b3
Revises: a5b6c7d8e9f0
Create Date: 2026-11-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: str | None = "a5b6c7d8e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_quota_counters",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "window_start"),
    )
    op.create_index(
        op.f("ix_ai_quota_counters_user_id"), "ai_quota_counters", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_quota_counters_user_id"), table_name="ai_quota_counters")
    op.drop_table("ai_quota_counters")
