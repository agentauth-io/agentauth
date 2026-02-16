"""add_api_keys_table

Revision ID: a3b4c5d6e7f8
Revises: e9fc446ffb64
Create Date: 2026-02-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'e9fc446ffb64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('api_keys',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_id', sa.String(length=16), nullable=False),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        sa.UniqueConstraint('key_id'),
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_owner'), 'api_keys', ['owner'], unique=False)
    op.create_index('ix_api_keys_active_hash', 'api_keys', ['key_hash', 'is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_api_keys_active_hash', table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_owner'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_table('api_keys')
