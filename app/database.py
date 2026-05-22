# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL directly from environment first
# This ensures Render's value always takes priority
database_url = os.environ.get("DATABASE_URL") or "sqlite:///./freelancer_hub.db"

# Render gives "postgres://" but SQLAlchemy needs "postgresql://"
database_url = database_url.replace("postgres://", "postgresql://", 1)

# CRITICAL: check_same_thread is ONLY for SQLite
# Never pass it to PostgreSQL — it will crash
if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL — no connect_args needed
    engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()