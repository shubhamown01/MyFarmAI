"""identity tables for passwordless email OTP (E1)

Owner-approved 2026-11-01: authentication_accounts (multi-provider account
links, provider values stored as plain strings so adding a provider never
requires a migration) + contact_verifications (one-time codes; single-use
consumption enforced in code).

Revision ID: b3f2a5d1c7e4
Revises: a7c1e409f2b3
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f2a5d1c7e4'
down_revision: Union[str, None] = 'a7c1e409f2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('authentication_accounts',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('provider_account_id', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider', 'provider_account_id', name='uq_authentication_accounts_provider_account')
    )
    op.create_index(op.f('ix_authentication_accounts_user_id'), 'authentication_accounts', ['user_id'], unique=False)

    op.create_table('contact_verifications',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('channel', sa.String(length=10), nullable=False),
    sa.Column('destination', sa.String(length=255), nullable=False),
    sa.Column('code_hash', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('max_attempts', sa.Integer(), server_default='5', nullable=False),
    sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_verifications_user_id'), 'contact_verifications', ['user_id'], unique=False)
    op.create_index('ix_contact_verifications_destination_consumed', 'contact_verifications', ['destination', 'consumed_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_contact_verifications_destination_consumed', table_name='contact_verifications')
    op.drop_index(op.f('ix_contact_verifications_user_id'), table_name='contact_verifications')
    op.drop_table('contact_verifications')
    op.drop_index(op.f('ix_authentication_accounts_user_id'), table_name='authentication_accounts')
    op.drop_table('authentication_accounts')
