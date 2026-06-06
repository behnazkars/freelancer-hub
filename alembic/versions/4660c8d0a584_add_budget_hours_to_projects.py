"""add_budget_hours_to_projects

Revision ID: 4660c8d0a584
Revises: cb72a21868bc
Create Date: 2026-06-05 07:38:53.555862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4660c8d0a584'
down_revision: Union[str, Sequence[str], None] = 'cb72a21868bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('budget_hours', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'budget_hours')
    # ### end Alembic commands ###
