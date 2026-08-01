"""enforce_not_null_constraints

Revision ID: 5c66f403d540
Revises: 12c7d87c5e63
Create Date: 2026-08-01 15:45:28.393684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c66f403d540'
down_revision: Union[str, Sequence[str], None] = '12c7d87c5e63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enforce NOT NULL on columns that were always meant to be required."""
    with op.batch_alter_table('invoices') as batch_op:
        batch_op.alter_column('tax_rate', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=9), nullable=False)

    with op.batch_alter_table('projects') as batch_op:
        batch_op.alter_column('hourly_rate', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('pricing_type', existing_type=sa.VARCHAR(length=6), nullable=False)
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=9), nullable=False)

    with op.batch_alter_table('time_entries') as batch_op:
        batch_op.alter_column('start_time', existing_type=sa.DATETIME(), nullable=False)
        batch_op.alter_column('end_time', existing_type=sa.DATETIME(), nullable=False)
        batch_op.alter_column('duration', existing_type=sa.FLOAT(), nullable=False)

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('is_active', existing_type=sa.BOOLEAN(), nullable=False)


def downgrade() -> None:
    """Revert columns back to nullable."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('is_active', existing_type=sa.BOOLEAN(), nullable=True)

    with op.batch_alter_table('time_entries') as batch_op:
        batch_op.alter_column('duration', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('end_time', existing_type=sa.DATETIME(), nullable=True)
        batch_op.alter_column('start_time', existing_type=sa.DATETIME(), nullable=True)

    with op.batch_alter_table('projects') as batch_op:
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=9), nullable=True)
        batch_op.alter_column('pricing_type', existing_type=sa.VARCHAR(length=6), nullable=True)
        batch_op.alter_column('hourly_rate', existing_type=sa.FLOAT(), nullable=True)

    with op.batch_alter_table('invoices') as batch_op:
        batch_op.alter_column('status', existing_type=sa.VARCHAR(length=9), nullable=True)
        batch_op.alter_column('tax_rate', existing_type=sa.FLOAT(), nullable=True)