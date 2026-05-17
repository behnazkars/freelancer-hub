# app/models/invoice.py
import enum
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)

    # Invoice number — shown on the actual invoice document
    # e.g. "INV-001", "INV-002"
    invoice_number = Column(String, nullable=False)

    amount = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)   # percentage e.g. 18.0 for 18%
    total_amount = Column(Float, nullable=False)

    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.draft)

    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)  # filled in when payment received

    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice id={self.id} number={self.invoice_number} status={self.status}>"