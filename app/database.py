# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# The Engine is the starting point of SQLAlchemy.
# It manages the connection to the database.
# We create it ONCE and reuse it for the entire app lifetime.
engine = create_engine(
    settings.database_url,
    # This line is SQLite-specific.
    # SQLite doesn't allow the same connection to be used
    # across multiple threads by default.
    # FastAPI uses multiple threads, so we need this.
    connect_args={"check_same_thread": False}
)

# A SessionLocal is a factory that creates new Session objects.
# Each request gets its own Session — think of it as
# a temporary workspace for database operations.
SessionLocal = sessionmaker(
    autocommit=False,  # we control when to save changes
    autoflush=False,   # we control when to send SQL to DB
    bind=engine        # connect it to our engine
)

# Base is the parent class all our models will inherit from.
# SQLAlchemy uses it to track all the tables we define.
Base = declarative_base()


# This is a "dependency" — FastAPI will call this function
# automatically for every request that needs DB access.
# The 'yield' makes it a generator:
#   1. Opens a session before the request
#   2. Hands it to the route handler
#   3. Closes it after the request (even if there's an error)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()