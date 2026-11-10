"""Add feedback table for tester submissions (E1).

Feedback is synthetic-safe: only category, message, email, and app version.
No passwords, OTPs, farm data, or unnecessary personal info stored.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.db.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "f4b2c3d4e5a7_fb_feedback1"
down_revision: str | None = "c8d9e0f1a2b3"
branch_labels: Sequence[str] = None
depends_on: Sequence[str] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.Index("ix_feedback_user_id", "user_id", unique=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
