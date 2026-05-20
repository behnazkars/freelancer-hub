# app/models/time_entry.py
from sqlalchemy import String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )

    # hours worked — using Float so you can log 1.5 hours etc.
    hours: Mapped[float] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Date (not DateTime) — just the calendar day, no time needed
    date: Mapped[str] = mapped_column(Date)

    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry id={self.id} hours={self.hours}>"