# app/models/client.py
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # ForeignKey links this row to a specific user
    # "users.id" means: the id column in the users table
    # ondelete="CASCADE" means: if the user is deleted,
    # all their clients are automatically deleted too
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships let you navigate between tables in Python
    # e.g. client.projects gives you all projects for this client
    # back_populates creates a two-way link
    owner = relationship("User", back_populates="clients")
    projects = relationship("Project", back_populates="client", cascade="all, delete")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete")

    def __repr__(self):
        return f"<Client id={self.id} name={self.name}>"