"""Invoice schemas."""
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.models.invoice import InvoiceStatus


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""
    amount: Decimal
    currency: str = "USD"
    vendor_id: Optional[int] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    description: Optional[str] = None


class InvoiceFilter(BaseModel):
    """Schema for filtering invoices."""
    status: Optional[InvoiceStatus] = None
    vendor_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    skip: int = 0
    limit: int = 100


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    id: int
    tenant_id: int
    vendor_id: Optional[int]
    invoice_number: Optional[str]
    amount: Decimal
    currency: str
    invoice_date: Optional[datetime]
    description: Optional[str]
    status: InvoiceStatus
    created_at: datetime

    class Config:
        from_attributes = True
