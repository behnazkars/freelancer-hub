"""add_pricing_type_to_projects

Revision ID: 12c7d87c5e63
Revises: 4660c8d0a584
Create Date: 2026-06-06 20:12:31.480194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '12c7d87c5e63'
down_revision: Union[str, Sequence[str], None] = '4660c8d0a584'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column(
        'pricing_type',
        sa.Enum('hourly', 'fixed', name='pricingtype'),
        nullable=True
    ))
    op.execute("UPDATE projects SET pricing_type = 'hourly' WHERE pricing_type IS NULL")


def downgrade() -> None:
    op.drop_column('projects', 'pricing_type')