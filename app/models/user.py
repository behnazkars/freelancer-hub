# app/models/user.py
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class User(Base):
    """
    The User table in the database.
    Each attribute = one column in the table.
    Mapped[type] is the modern SQLAlchemy 2.0 style —
    it tells both SQLAlchemy and the type checker the exact
    Python type of each column, eliminating type warnings.
    """
    __tablename__ = "users"  # the actual table name in SQLite

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # func.now() automatically sets the time on the database side
    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # These tell SQLAlchemy: "a User has many of these"
    # Now you can do: user.clients, user.projects, etc.
    clients = relationship("Client", back_populates="owner", cascade="all, delete")
    projects = relationship("Project", back_populates="owner", cascade="all, delete")
    time_entries = relationship("TimeEntry", back_populates="owner", cascade="all, delete")
    invoices = relationship("Invoice", back_populates="owner", cascade="all, delete")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"