# app/models/time_entry.py
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey
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

    # --- NEW: replace hours + date with start/end/duration ---
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time:   Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration:   Mapped[float]   = mapped_column(Float)   # stored in hours, auto-calculated
    # ---------------------------------------------------------

    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    owner   = relationship("User",    back_populates="time_entries")
    project = relationship("Project", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry id={self.id} duration={self.duration}h>"