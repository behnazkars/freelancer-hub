# app/schemas/client.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ─── Request schemas ──────────────────────────────────────────────

class ClientCreate(BaseModel):
    """Data required to create a new client."""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    """
    All fields are Optional here — this allows partial updates.
    The client only sends the fields they want to change.
    This is the pattern for PATCH requests.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


# ─── Response schemas ─────────────────────────────────────────────

class ClientResponse(BaseModel):
    """What we return when someone asks for a client."""
    id: int
    user_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True