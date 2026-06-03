# alembic/versions/cb72a21868bc_replace_hours_date_with_start_end_.py
"""replace_hours_date_with_start_end_duration

Revision ID: cb72a21868bc
Revises: 
Create Date: 2026-06-03 20:05:42.331425
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cb72a21868bc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace hours + date columns with start_time, end_time, duration."""
    from alembic import op
    import sqlalchemy as sa

    # Step 1: Add new columns as NULLABLE first
    op.add_column('time_entries', sa.Column('start_time', sa.DateTime(timezone=True), nullable=True))
    op.add_column('time_entries', sa.Column('end_time',   sa.DateTime(timezone=True), nullable=True))
    op.add_column('time_entries', sa.Column('duration',   sa.Float(),                 nullable=True))

    # Step 2: Fill existing rows — different SQL for SQLite vs PostgreSQL
    bind = op.get_bind()
    dialect = bind.dialect.name   # "sqlite" or "postgresql"

    if dialect == "sqlite":
        op.execute("""
            UPDATE time_entries
            SET
                start_time = datetime(date, '09:00:00'),
                end_time   = datetime(date, '09:00:00', '+' || CAST(CAST(hours AS INTEGER) AS TEXT) || ' hours'),
                duration   = hours
            WHERE start_time IS NULL
        """)
    else:
        # PostgreSQL syntax
        op.execute("""
            UPDATE time_entries
            SET
                start_time = (date || ' 09:00:00')::timestamp,
                end_time   = (date || ' 09:00:00')::timestamp + (hours * interval '1 hour'),
                duration   = hours
            WHERE start_time IS NULL
        """)

    # Step 3: Drop old columns
    op.drop_column('time_entries', 'hours')
    op.drop_column('time_entries', 'date')


def downgrade() -> None:
    """Restore hours + date columns."""
    op.add_column('time_entries', sa.Column('date',  sa.DATE(),  nullable=True))
    op.add_column('time_entries', sa.Column('hours', sa.FLOAT(), nullable=True))
    op.drop_column('time_entries', 'duration')
    op.drop_column('time_entries', 'end_time')
    op.drop_column('time_entries', 'start_time')