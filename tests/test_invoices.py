"""Tests for invoice endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime
from app.models.invoice import InvoiceStatus


def test_create_invoice(client, tenant):
    """Test creating an invoice."""
    response = client.post(
        f"/tenants/{tenant.id}/invoices",
        json={
            "amount": "100.50",
            "currency": "USD",
            "invoice_number": "INV-001",
            "description": "Test invoice",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "100.50"
    assert data["currency"] == "USD"
    assert data["invoice_number"] == "INV-001"
    assert data["status"] == "open"
    assert data["tenant_id"] == tenant.id


def test_list_invoices(client, tenant, vendor):
    """Test listing invoices."""
    # Create multiple invoices
    client.post(
        f"/tenants/{tenant.id}/invoices",
        json={
            "amount": "100.00",
            "vendor_id": vendor.id,
            "status": "open",
        },
    )
    client.post(
        f"/tenants/{tenant.id}/invoices",
        json={
            "amount": "200.00",
            "status": "open",
        },
    )

    # List all invoices
    response = client.get(f"/tenants/{tenant.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Filter by vendor
    response = client.get(
        f"/tenants/{tenant.id}/invoices?vendor_id={vendor.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["vendor_id"] == vendor.id

    # Filter by status
    response = client.get(
        f"/tenants/{tenant.id}/invoices?status=open"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(inv["status"] == "open" for inv in data)

    # Filter by amount range
    response = client.get(
        f"/tenants/{tenant.id}/invoices?min_amount=150.00&max_amount=250.00"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == "200.00"


def test_delete_invoice(client, tenant):
    """Test deleting an invoice."""
    # Create invoice
    response = client.post(
        f"/tenants/{tenant.id}/invoices",
        json={"amount": "100.00"},
    )
    assert response.status_code == 201
    invoice_id = response.json()["id"]

    # Delete invoice
    response = client.delete(f"/tenants/{tenant.id}/invoices/{invoice_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/tenants/{tenant.id}/invoices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

    # Try to delete non-existent invoice
    response = client.delete(f"/tenants/{tenant.id}/invoices/999")
    assert response.status_code == 404
