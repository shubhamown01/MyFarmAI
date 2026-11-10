"""E5 farmer profile: farmer_profiles table

One progressive farmer profile per user. Optional fields per directive §8 —
no mandatory agricultural data beyond the core onboarding flow.

Revision ID: a5b6c7d8e9f0
Revises: f4b2c3d4e5a6
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5b6c7d8e9f0"
down_revision: str | None = "f4b2c3d4e5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "farmer_profiles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("farming_type", sa.String(length=50), nullable=True),
        sa.Column("preferred_language", sa.String(length=10), nullable=True),
        sa.Column("farming_experience_years", sa.Integer(), nullable=True),
        sa.Column("existing_crops", sa.JSON(), nullable=True),
        sa.Column("intended_crops", sa.JSON(), nullable=True),
        sa.Column("soil_info", sa.String(length=500), nullable=True),
        sa.Column("water_availability", sa.String(length=100), nullable=True),
        sa.Column("growing_season", sa.String(length=100), nullable=True),
        sa.Column("profile_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "farming_type IN ('home_farming', 'small_outdoor', 'agricultural', 'other')",
            name="ck_farmer_profiles_farming_type",
        ),
        sa.CheckConstraint(
            "farming_experience_years IS NULL OR (farming_experience_years >= 0 AND farming_experience_years <= 100)",
            name="ck_farmer_profiles_experience",
        ),
    )
    op.create_index(op.f("ix_farmer_profiles_user_id"), "farmer_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_farmer_profiles_user_id"), table_name="farmer_profiles")
    op.drop_table("farmer_profiles")
