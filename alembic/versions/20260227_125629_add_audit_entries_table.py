"""add_audit_entries_table

Revision ID: 39a1b661b352
Revises: 20260216_130000_add_api_key_expires_at
Create Date: 2026-02-27 12:56:29.090554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39a1b661b352'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_entries table
    op.create_table(
        'audit_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_id', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('actor_id', sa.String(255), nullable=False, index=True),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True, index=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('signature', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'), index=True),
    )

    # Create composite indexes for common queries
    op.create_index('ix_audit_event_type_created', 'audit_entries', ['event_type', 'created_at'])
    op.create_index('ix_audit_actor_created', 'audit_entries', ['actor_id', 'created_at'])
    op.create_index('ix_audit_outcome_created', 'audit_entries', ['outcome', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_outcome_created', table_name='audit_entries')
    op.drop_index('ix_audit_actor_created', table_name='audit_entries')
    op.drop_index('ix_audit_event_type_created', table_name='audit_entries')

    # Drop table
    op.drop_table('audit_entries')
