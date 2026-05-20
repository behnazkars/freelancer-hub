# app/services/invoice_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.invoice import Invoice, InvoiceStatus
from app.models.client import Client
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


def get_all_invoices(db: Session, user_id: int) -> list[Invoice]:
    """Get all invoices for the logged-in user."""
    return db.query(Invoice).filter(Invoice.user_id == user_id).all()


def get_invoice_by_id(db: Session, invoice_id: int, user_id: int) -> Invoice:
    """Get a single invoice — always filter by user_id for security."""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == user_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


def create_invoice(
    db: Session,
    invoice_data: InvoiceCreate,
    user_id: int
) -> Invoice:
    """
    Create a new invoice.
    Automatically calculates total_amount from amount + tax_rate.
    Verifies the client belongs to this user.
    """
    # Security check — client must belong to this user
    client = db.query(Client).filter(
        Client.id == invoice_data.client_id,
        Client.user_id == user_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or does not belong to you"
        )

    # Calculate total automatically
    # e.g. amount=1000, tax_rate=18 → total = 1000 + (1000 * 18/100) = 1180
    tax_amount = invoice_data.amount * (invoice_data.tax_rate or 0) / 100
    total_amount = invoice_data.amount + tax_amount

    new_invoice = Invoice(
        **invoice_data.model_dump(),
        user_id=user_id,
        total_amount=total_amount,
        status=InvoiceStatus.draft  # always starts as draft
    )
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    return new_invoice


def update_invoice(
    db: Session,
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    user_id: int
) -> Invoice:
    """
    Update an invoice.
    Recalculates total_amount if amount or tax_rate changes.
    """
    invoice = get_invoice_by_id(db, invoice_id, user_id)

    update_data = invoice_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Recalculate total if amount or tax changed
    if "amount" in update_data or "tax_rate" in update_data:
        tax_amount = invoice.amount * (invoice.tax_rate or 0) / 100
        invoice.total_amount = invoice.amount + tax_amount

    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice_id: int, user_id: int) -> dict:
    """Delete an invoice."""
    invoice = get_invoice_by_id(db, invoice_id, user_id)
    db.delete(invoice)
    db.commit()
    return {"message": f"Invoice {invoice.invoice_number} deleted successfully"}