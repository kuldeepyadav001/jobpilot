"""add message_id to responses for duplicate-email prevention

Revision ID: a2b3c4d5e6f7
Revises: 03d3d0cc6aed
Create Date: 2026-08-30 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '03d3d0cc6aed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('responses', sa.Column('message_id', sa.String(length=500), nullable=True))
    op.create_index(op.f('ix_responses_message_id'), 'responses', ['message_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_responses_message_id'), table_name='responses')
    op.drop_column('responses', 'message_id')
