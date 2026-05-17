# app/models/project.py
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# Using Python Enum for status keeps values consistent
# The database only accepts these exact strings — no typos possible
class ProjectStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    on_hold = "on_hold"
    cancelled = "cancelled"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # hourly_rate is what you charge per hour for this project
    hourly_rate = Column(Float, default=0.0)

    # budget is the total agreed amount (optional)
    budget = Column(Float, nullable=True)

    status = Column(Enum(ProjectStatus), default=ProjectStatus.active)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    time_entries = relationship("TimeEntry", back_populates="project", cascade="all, delete")

    def __repr__(self):
        return f"<Project id={self.id} name={self.name}>"