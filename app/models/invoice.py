# app/models/invoice.py
import enum
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional

from app.database import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE")
    )

    # Invoice number — shown on the actual invoice document
    # e.g. "INV-001", "INV-002"
    invoice_number: Mapped[str] = mapped_column(String)

    amount: Mapped[float] = mapped_column(Float)
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0)  # e.g. 18.0 for 18%
    total_amount: Mapped[float] = mapped_column(Float)

    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), default=InvoiceStatus.draft
    )

    issue_date: Mapped[str] = mapped_column(Date)
    due_date: Mapped[str] = mapped_column(Date)
    paid_date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)  # filled when paid

    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    owner = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice id={self.id} number={self.invoice_number}>"