# app/routers/invoices.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services.invoice_service import (
    get_all_invoices,
    get_invoice_by_id,
    create_invoice,
    update_invoice,
    delete_invoice
)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/", response_model=list[InvoiceResponse])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all invoices for the logged-in user."""
    return get_all_invoices(db, current_user.id)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single invoice by ID."""
    return get_invoice_by_id(db, invoice_id, current_user.id)


@router.post("/", response_model=InvoiceResponse, status_code=201)
def create_new_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invoice. Total is calculated automatically."""
    return create_invoice(db, invoice_data, current_user.id)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_existing_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an invoice. Only send fields you want to change."""
    return update_invoice(db, invoice_id, invoice_data, current_user.id)


@router.delete("/{invoice_id}")
def delete_existing_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an invoice."""
    return delete_invoice(db, invoice_id, current_user.id)