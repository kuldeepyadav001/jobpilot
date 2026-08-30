"""add job_type to jobs

Revision ID: b4e6c8d9a1f2
Revises: a2b3c4d5e6f7
Create Date: 2026-08-31 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e6c8d9a1f2'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('job_type', sa.String(length=20), server_default='job', nullable=False))
    op.create_index(op.f('ix_jobs_job_type'), 'jobs', ['job_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_jobs_job_type'), table_name='jobs')
    op.drop_column('jobs', 'job_type')
