# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    The User table in the database.
    Each attribute = one column in the table.
    """
    __tablename__ = "users"  # the actual table name in SQLite

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # func.now() automatically sets the time on the database side
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # These tell SQLAlchemy: "a User has many of these"
    # Now you can do: user.clients, user.projects, etc.
    clients = relationship("Client", back_populates="owner", cascade="all, delete")
    projects = relationship("Project", back_populates="owner", cascade="all, delete")
    time_entries = relationship("TimeEntry", back_populates="owner", cascade="all, delete")
    invoices = relationship("Invoice", back_populates="owner", cascade="all, delete")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"