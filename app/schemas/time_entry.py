# app/schemas/time_entry.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class TimeEntryCreate(BaseModel):
    project_id: int
    hours: float
    description: Optional[str] = None
    date: date


class TimeEntryUpdate(BaseModel):
    project_id:  Optional[int]   = None
    hours:       Optional[float] = None
    description: Optional[str]   = None
    date:        Optional[str]   = None  # string to avoid Pydantic v2 Optional[date] bug


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