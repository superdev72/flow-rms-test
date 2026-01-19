"""Invoice model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration."""
    OPEN = "open"
    MATCHED = "matched"
    PAID = "paid"


class Invoice(Base):
    """Invoice model."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True)
    invoice_number = Column(String, nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD", nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    description = Column(String, nullable=True)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.OPEN, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    matches = relationship("Match", back_populates="invoice")
