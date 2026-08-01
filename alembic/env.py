# alembic/env.py
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make sure Python can find your app ──────────────────────────────────
# This adds the project root to sys.path so we can import from app/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Import your models and Base ─────────────────────────────────────────
# We must import Base AND all models so Alembic can see the full schema
from app.database import Base
from app.models import user, client, project, time_entry, invoice

# ── Alembic Config object ────────────────────────────────────────────────
config = context.config

# ── Use your app's DATABASE_URL if set (overrides alembic.ini) ──────────
# This makes Alembic work on Render with PostgreSQL automatically
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Render gives "postgres://" but SQLAlchemy needs "postgresql://"
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

# ── Logging ──────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── This is what tells Alembic about your tables ─────────────────────────
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection — just generates SQL."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection — the normal mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()