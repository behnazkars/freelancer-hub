# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ─── Request schemas (what the client sends) ──────────────────────

class UserRegister(BaseModel):
    """Data required to create a new account."""
    full_name: str
    email: EmailStr        # EmailStr validates it's a real email format
    password: str


class UserLogin(BaseModel):
    """Data required to log in."""
    email: EmailStr
    password: str


# ─── Response schemas (what we send back) ────────────────────────

class UserResponse(BaseModel):
    """
    Safe user data to return in API responses.
    Notice: hashed_password is NOT here — never expose it.
    """
    id: int
    full_name: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        # Allows Pydantic to read data from SQLAlchemy model objects
        # Without this, Pydantic only reads plain dicts
        from_attributes = True


class TokenResponse(BaseModel):
    """The JWT token returned after successful login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from inside a JWT token."""
    email: Optional[str] = None