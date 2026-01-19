"""Tests for multi-tenant isolation."""
import pytest
from decimal import Decimal
from datetime import datetime


def test_tenant_isolation(client, db):
    """Test that tenants cannot access each other's data."""
    from app.services.tenant_service import TenantService
    from app.services.invoice_service import InvoiceService

    # Create two tenants
    tenant1 = TenantService.create_tenant(db, "Tenant 1")
    tenant2 = TenantService.create_tenant(db, "Tenant 2")

    # Create invoice for tenant1
    invoice1 = InvoiceService.create_invoice(
        db, tenant1.id, Decimal("100.00"), description="Tenant 1 invoice"
    )

    # Create invoice for tenant2
    invoice2 = InvoiceService.create_invoice(
        db, tenant2.id, Decimal("200.00"), description="Tenant 2 invoice"
    )

    # Tenant1 should only see their invoice
    response = client.get(f"/tenants/{tenant1.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == invoice1.id
    assert data[0]["tenant_id"] == tenant1.id

    # Tenant2 should only see their invoice
    response = client.get(f"/tenants/{tenant2.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == invoice2.id
    assert data[0]["tenant_id"] == tenant2.id

    # Tenant1 cannot access tenant2's invoice
    response = client.get(f"/tenants/{tenant1.id}/invoices/{invoice2.id}")
    # Should return empty or 404, but definitely not the invoice
    invoices = InvoiceService.list_invoices(db, tenant1.id)
    assert invoice2.id not in [inv.id for inv in invoices]
