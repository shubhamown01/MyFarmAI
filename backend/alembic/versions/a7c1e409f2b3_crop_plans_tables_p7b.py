"""crop_plans tables (P7B)

Owner-approved 2026-11-01 (FCL-080): crop_plans + crop_plan_tasks +
crop_plan_revisions. Farmer-controlled plans with append-only change
history; user tasks never auto-modified; soft-cancel only.

Revision ID: a7c1e409f2b3
Revises: 6cd2bffd9881
Create Date: 2026-11-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c1e409f2b3'
down_revision: Union[str, None] = '6cd2bffd9881'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('crop_plans',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('farm_id', sa.UUID(), nullable=False),
    sa.Column('crop_cycle_id', sa.UUID(), nullable=True),
    sa.Column('variety', sa.String(length=100), nullable=True),
    sa.Column('planting_date', sa.Date(), nullable=True),
    sa.Column('assumptions', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['crop_cycle_id'], ['crop_cycles.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_plans_user_id'), 'crop_plans', ['user_id'], unique=False)
    op.create_index(op.f('ix_crop_plans_farm_id'), 'crop_plans', ['farm_id'], unique=False)

    op.create_table('crop_plan_tasks',
    sa.Column('plan_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('source', sa.Enum('USER', 'SUGGESTED', name='cropplantasksource', native_enum=False), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'DONE', 'CANCELLED', name='cropplantaskstatus', native_enum=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['crop_plans.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_plan_tasks_plan_id'), 'crop_plan_tasks', ['plan_id'], unique=False)

    op.create_table('crop_plan_revisions',
    sa.Column('plan_id', sa.UUID(), nullable=False),
    sa.Column('changed_by', sa.UUID(), nullable=False),
    sa.Column('summary', sa.String(length=500), nullable=False),
    sa.Column('snapshot', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['plan_id'], ['crop_plans.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crop_plan_revisions_plan_id'), 'crop_plan_revisions', ['plan_id'], unique=False)


def downgrade() -> None:
    op.drop_table('crop_plan_revisions')
    op.drop_table('crop_plan_tasks')
    op.drop_table('crop_plans')
    sa.Enum(name='cropplantasksource').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='cropplantaskstatus').drop(op.get_bind(), checkfirst=True)
