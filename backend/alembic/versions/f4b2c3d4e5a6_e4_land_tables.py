"""E4 land tables: home_locations, farm_plots, farm_boundaries, farm_area_measurements

Owner-approved (2026-11-01): staged schema program with NO PostGIS —
polygons stored as lat/lon JSON, geodesic area computed in Python.
home_locations is separate from farms (a farmer's home is never assumed
to be on their farmland).

Revision ID: f4b2c3d4e5a6
Revises: e3a1b2c3d4e5
Create Date: 2026-11-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4b2c3d4e5a6"
down_revision: str | None = "e3a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "home_locations",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="true", nullable=False),
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
            "source IN ('auto_detected', 'manual_entry', 'map_pin')",
            name="ck_home_locations_source",
        ),
    )
    op.create_index(op.f("ix_home_locations_user_id"), "home_locations", ["user_id"], unique=False)
    op.create_index(
        "ix_home_locations_user_primary", "home_locations", ["user_id", "is_primary"], unique=False
    )

    op.create_table(
        "farm_plots",
        sa.Column("farm_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("land_type", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
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
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "land_type IN ('home_farming', 'small_outdoor', 'agricultural', 'other')",
            name="ck_farm_plots_land_type",
        ),
    )
    op.create_index(op.f("ix_farm_plots_farm_id"), "farm_plots", ["farm_id"], unique=False)
    op.create_index("ix_farm_plots_farm_name", "farm_plots", ["farm_id", "name"], unique=False)

    op.create_table(
        "farm_area_measurements",
        sa.Column("plot_id", sa.UUID(), nullable=False),
        sa.Column("area_sq_m", sa.Float(), nullable=False),
        sa.Column("area_unit", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("user_confirmed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["plot_id"], ["farm_plots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "source IN ('map_measured', 'user_reported')",
            name="ck_farm_area_measurements_source",
        ),
        sa.CheckConstraint(
            "area_unit IN ('sq_m', 'sq_km', 'hectare', 'acre', 'sq_ft', 'sq_yd')",
            name="ck_farm_area_measurements_unit",
        ),
    )
    op.create_index(
        op.f("ix_farm_area_measurements_plot_id"),
        "farm_area_measurements",
        ["plot_id"],
        unique=False,
    )
    op.create_index(
        "ix_farm_area_measurements_plot_created",
        "farm_area_measurements",
        ["plot_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "farm_boundaries",
        sa.Column("plot_id", sa.UUID(), nullable=False),
        sa.Column("polygon", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("point_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["plot_id"], ["farm_plots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "source IN ('map_drawn', 'manual_entry')",
            name="ck_farm_boundaries_source",
        ),
    )
    op.create_index(op.f("ix_farm_boundaries_plot_id"), "farm_boundaries", ["plot_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_farm_boundaries_plot_id"), table_name="farm_boundaries")
    op.drop_table("farm_boundaries")
    op.drop_index("ix_farm_area_measurements_plot_created", table_name="farm_area_measurements")
    op.drop_index(op.f("ix_farm_area_measurements_plot_id"), table_name="farm_area_measurements")
    op.drop_table("farm_area_measurements")
    op.drop_index("ix_farm_plots_farm_name", table_name="farm_plots")
    op.drop_index(op.f("ix_farm_plots_farm_id"), table_name="farm_plots")
    op.drop_table("farm_plots")
    op.drop_index("ix_home_locations_user_primary", table_name="home_locations")
    op.drop_index(op.f("ix_home_locations_user_id"), table_name="home_locations")
    op.drop_table("home_locations")
