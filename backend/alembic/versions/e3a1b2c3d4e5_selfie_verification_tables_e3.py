"""selfie verification tables + users.verification_status (E3 wave 1)

Owner-approved per E3_SELFIE_SECURITY_REVIEW (2026-11-01): consent_records,
selfie_verifications (status CHECK-constrained; storage_path is
server-internal and never exposed by the API), verification_events (audit
trail), and users.verification_status ('active' default for existing and
admin-created users; self-signups move to 'pending_verification' in code).

Revision ID: e3a1b2c3d4e5
Revises: b3f2a5d1c7e4
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a1b2c3d4e5'
down_revision: Union[str, None] = 'b3f2a5d1c7e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('verification_status', sa.String(length=20), server_default='active', nullable=False),
    )
    op.create_index(op.f('ix_users_verification_status'), 'users', ['verification_status'], unique=False)

    op.create_table('consent_records',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('consent_type', sa.String(length=50), nullable=False),
    sa.Column('policy_version', sa.String(length=20), nullable=False),
    sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consent_records_user_id'), 'consent_records', ['user_id'], unique=False)
    op.create_index('ix_consent_records_user_type', 'consent_records', ['user_id', 'consent_type'], unique=False)

    op.create_table('selfie_verifications',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('challenge_id', sa.String(length=64), nullable=False),
    sa.Column('storage_path', sa.String(length=512), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('challenge_completed', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('vl_hint', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='pending_review', nullable=False),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rejection_reason', sa.String(length=255), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.CheckConstraint("status IN ('pending_review', 'approved', 'rejected')", name='ck_selfie_verifications_status')
    )
    op.create_index(op.f('ix_selfie_verifications_user_id'), 'selfie_verifications', ['user_id'], unique=False)
    op.create_index('ix_selfie_verifications_user_status', 'selfie_verifications', ['user_id', 'status'], unique=False)
    op.create_index('ix_selfie_verifications_status', 'selfie_verifications', ['status'], unique=False)

    op.create_table('verification_events',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_events_user_id'), 'verification_events', ['user_id'], unique=False)
    op.create_index('ix_verification_events_user_created', 'verification_events', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_verification_events_user_created', table_name='verification_events')
    op.drop_index(op.f('ix_verification_events_user_id'), table_name='verification_events')
    op.drop_table('verification_events')
    op.drop_index('ix_selfie_verifications_status', table_name='selfie_verifications')
    op.drop_index('ix_selfie_verifications_user_status', table_name='selfie_verifications')
    op.drop_index(op.f('ix_selfie_verifications_user_id'), table_name='selfie_verifications')
    op.drop_table('selfie_verifications')
    op.drop_index('ix_consent_records_user_type', table_name='consent_records')
    op.drop_index(op.f('ix_consent_records_user_id'), table_name='consent_records')
    op.drop_table('consent_records')
    op.drop_index(op.f('ix_users_verification_status'), table_name='users')
    op.drop_column('users', 'verification_status')
