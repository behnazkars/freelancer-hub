# app/schemas/time_entry.py
from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional


class TimeEntryCreate(BaseModel):
    project_id:  int
    start_time:  datetime
    end_time:    datetime
    description: Optional[str] = None

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "TimeEntryCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class TimeEntryUpdate(BaseModel):
    start_time:  Optional[datetime] = None
    end_time:    Optional[datetime] = None
    description: Optional[str]     = None

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "TimeEntryUpdate":
        # Only validate if BOTH are provided
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
        return self


class TimeEntryResponse(BaseModel):
    id:          int
    user_id:     int
    project_id:  int
    start_time:  datetime
    end_time:    datetime
    duration:    float        # hours, e.g. 2.5
    description: Optional[str] = None
    created_at:  datetime

    class Config:
        from_attributes = True