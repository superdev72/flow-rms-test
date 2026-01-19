"""Invoice service."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models.invoice import Invoice, InvoiceStatus
from app.models.tenant import Tenant


class InvoiceService:
    """Service for invoice operations."""

    @staticmethod
    def create_invoice(
        db: Session,
        tenant_id: int,
        amount: Decimal,
        currency: str = "USD",
        vendor_id: Optional[int] = None,
        invoice_number: Optional[str] = None,
        invoice_date: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> Invoice:
        """Create a new invoice."""
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        invoice = Invoice(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            invoice_number=invoice_number,
            amount=amount,
            currency=currency,
            invoice_date=invoice_date,
            description=description,
            status=InvoiceStatus.OPEN,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_invoice(db: Session, tenant_id: int, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID, ensuring tenant isolation."""
        return (
            db.query(Invoice)
            .filter(and_(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id))
            .first()
        )

    @staticmethod
    def list_invoices(
        db: Session,
        tenant_id: int,
        status: Optional[InvoiceStatus] = None,
        vendor_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """List invoices with filtering, ensuring tenant isolation."""
        query = db.query(Invoice).filter(Invoice.tenant_id == tenant_id)

        if status:
            query = query.filter(Invoice.status == status)
        if vendor_id:
            query = query.filter(Invoice.vendor_id == vendor_id)
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
        if min_amount:
            query = query.filter(Invoice.amount >= min_amount)
        if max_amount:
            query = query.filter(Invoice.amount <= max_amount)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def delete_invoice(db: Session, tenant_id: int, invoice_id: int) -> bool:
        """Delete an invoice, ensuring tenant isolation."""
        invoice = InvoiceService.get_invoice(db, tenant_id, invoice_id)
        if not invoice:
            return False
        db.delete(invoice)
        db.commit()
        return True
