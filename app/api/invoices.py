"""Invoice REST endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceFilter
from app.models.invoice import InvoiceStatus

router = APIRouter(prefix="/tenants/{tenant_id}/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    tenant_id: int,
    invoice: InvoiceCreate,
    db: Session = Depends(get_db),
):
    """Create a new invoice."""
    try:
        return InvoiceService.create_invoice(
            db,
            tenant_id,
            invoice.amount,
            invoice.currency,
            invoice.vendor_id,
            invoice.invoice_number,
            invoice.invoice_date,
            invoice.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    tenant_id: int,
    status: Optional[InvoiceStatus] = Query(None),
    vendor_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List invoices with filtering."""
    return InvoiceService.list_invoices(
        db,
        tenant_id,
        status=status,
        vendor_id=vendor_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        skip=skip,
        limit=limit,
    )


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(
    tenant_id: int,
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """Delete an invoice."""
    success = InvoiceService.delete_invoice(db, tenant_id, invoice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice not found")
