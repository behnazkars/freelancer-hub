# app/schemas/project.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.project import ProjectStatus, PricingType


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: int
    hourly_rate: Optional[float] = 0.0
    budget: Optional[float] = None
    budget_hours: Optional[float] = None
    pricing_type: Optional[PricingType] = PricingType.hourly
    status: Optional[ProjectStatus] = ProjectStatus.active


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    hourly_rate: Optional[float] = None
    budget: Optional[float] = None
    budget_hours: Optional[float] = None
    pricing_type: Optional[PricingType] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    client_id: int
    name: str
    description: Optional[str] = None
    hourly_rate: float
    budget: Optional[float] = None
    budget_hours: Optional[float] = None
    pricing_type: PricingType
    status: ProjectStatus
    created_at: datetime

    class Config:
        from_attributes = True