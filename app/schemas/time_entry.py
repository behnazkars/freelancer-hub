# app/schemas/time_entry.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


# ─── Request schemas ──────────────────────────────────────────────

class TimeEntryCreate(BaseModel):
    """Data required to log a new time entry."""
    project_id: int
    hours: float
    description: Optional[str] = None
    date: date  # expects format: "2024-01-15"


class TimeEntryUpdate(BaseModel):
    """All fields optional — only send what you want to change."""
    hours: Optional[float] = None
    description: Optional[str] = None
    date: Optional[date] = None


# ─── Response schemas ─────────────────────────────────────────────

class TimeEntryResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    hours: float
    description: Optional[str] = None
    date: date
    created_at: datetime

    class Config:
        from_attributes = True