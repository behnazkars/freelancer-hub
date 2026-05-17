# app/models/time_entry.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # hours worked — using Float so you can log 1.5 hours etc.
    hours = Column(Float, nullable=False)
    description = Column(String, nullable=True)

    # Date (not DateTime) — just the calendar day, no time needed
    date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry id={self.id} hours={self.hours}>"