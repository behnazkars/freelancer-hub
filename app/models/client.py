# app/models/client.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # ForeignKey links this row to a specific user
    # "users.id" means: the id column in the users table
    # ondelete="CASCADE" means: if the user is deleted,
    # all their clients are automatically deleted too
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships let you navigate between tables in Python
    # e.g. client.projects gives you all projects for this client
    # back_populates creates a two-way link
    owner = relationship("User", back_populates="clients")
    projects = relationship("Project", back_populates="client", cascade="all, delete")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete")

    def __repr__(self):
        return f"<Client id={self.id} name={self.name}>"