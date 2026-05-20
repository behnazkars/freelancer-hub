# app/schemas/project.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: int
    hourly_rate: Optional[float] = 0.0
    budget: Optional[float] = None
    status: Optional[ProjectStatus] = ProjectStatus.active


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Optional[float] = None
    budget: Optional[float] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    client_id: int
    name: str
    description: Optional[str] = None
    hourly_rate: float
    budget: Optional[float] = None
    status: ProjectStatus
    created_at: datetime

    class Config:
        from_attributes = True