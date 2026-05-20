# app/schemas/invoice.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from app.models.invoice import InvoiceStatus


# ─── Request schemas ──────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    """Data required to create a new invoice."""
    client_id: int
    invoice_number: str       # e.g. "INV-001"
    amount: float
    tax_rate: Optional[float] = 0.0
    issue_date: date
    due_date: date
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """All fields optional for partial updates."""
    invoice_number: Optional[str] = None
    amount: Optional[float] = None
    tax_rate: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    notes: Optional[str] = None


# ─── Response schemas ─────────────────────────────────────────────

class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    client_id: int
    invoice_number: str
    amount: float
    tax_rate: float
    total_amount: float
    status: InvoiceStatus
    issue_date: date
    due_date: date
    paid_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True