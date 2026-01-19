"""Tests for reconciliation endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.models.invoice import InvoiceStatus
from app.models.match import MatchStatus


def test_reconciliation_produces_candidates(client, tenant, vendor, db):
    """Test that reconciliation produces match candidates with expected ranking."""
    from app.services.invoice_service import InvoiceService
    from app.services.transaction_service import TransactionService

    # Create invoices
    invoice1 = InvoiceService.create_invoice(
        db,
        tenant.id,
        Decimal("100.00"),
        vendor_id=vendor.id,
        invoice_number="INV-001",
        invoice_date=datetime.now(),
        description="Office supplies",
    )

    invoice2 = InvoiceService.create_invoice(
        db,
        tenant.id,
        Decimal("200.00"),
        vendor_id=vendor.id,
        invoice_number="INV-002",
        invoice_date=datetime.now(),
        description="Software license",
    )

    # Create transactions
    # Perfect match for invoice1
    transaction1_data = {
        "external_id": "TX-001",
        "posted_at": datetime.now().isoformat(),
        "amount": 100.00,
        "currency": "USD",
        "description": f"Payment to {vendor.name} - Office supplies",
    }

    # Partial match for invoice2
    transaction2_data = {
        "external_id": "TX-002",
        "posted_at": (datetime.now() + timedelta(days=2)).isoformat(),
        "amount": 200.00,
        "currency": "USD",
        "description": "Software payment",
    }

    # Import transactions
    TransactionService.import_transactions(
        db,
        tenant.id,
        [transaction1_data, transaction2_data],
    )[0]  # Unpack tuple, get the list

    # Run reconciliation
    response = client.post(f"/tenants/{tenant.id}/reconcile")
    assert response.status_code == 200
    data = response.json()
    matches = data["matches"]

    # Should have matches
    assert len(matches) >= 1

    # Find match for invoice1 (should have high score)
    invoice1_match = next(
        (m for m in matches if m["invoice_id"] == invoice1.id), None
    )
    assert invoice1_match is not None
    assert float(invoice1_match["score"]) >= 30.0  # Minimum threshold


def test_confirm_match(client, tenant, vendor, db):
    """Test confirming a match updates expected state."""
    from app.services.invoice_service import InvoiceService
    from app.services.transaction_service import TransactionService
    from app.services.reconciliation_service import ReconciliationService

    # Create invoice
    invoice = InvoiceService.create_invoice(
        db,
        tenant.id,
        Decimal("100.00"),
        vendor_id=vendor.id,
        invoice_date=datetime.now(),
        description="Test invoice",
    )

    # Create transaction
    transaction_data = {
        "external_id": "TX-001",
        "posted_at": datetime.now().isoformat(),
        "amount": 100.00,
        "currency": "USD",
        "description": f"Payment to {vendor.name}",
    }
    TransactionService.import_transactions(
        db, tenant.id, [transaction_data]
    )[0]  # Unpack tuple, get the list

    # Run reconciliation
    matches = ReconciliationService.reconcile(db, tenant.id)
    assert len(matches) > 0
    match_id = matches[0].id

    # Verify invoice is still open
    invoice = InvoiceService.get_invoice(db, tenant.id, invoice.id)
    assert invoice.status == InvoiceStatus.OPEN

    # Confirm match
    response = client.post(
        f"/tenants/{tenant.id}/reconcile/matches/{match_id}/confirm"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"

    # Verify invoice status updated
    invoice = InvoiceService.get_invoice(db, tenant.id, invoice.id)
    assert invoice.status == InvoiceStatus.MATCHED


def test_explain_reconciliation_mocked(client, tenant, vendor, db, monkeypatch):
    """Test AI explanation endpoint with mocked AI."""
    from app.services.invoice_service import InvoiceService
    from app.services.transaction_service import TransactionService

    # Create invoice
    invoice = InvoiceService.create_invoice(
        db,
        tenant.id,
        Decimal("100.00"),
        vendor_id=vendor.id,
        invoice_date=datetime.now(),
        description="Office supplies",
    )

    # Create transaction
    transaction_data = {
        "external_id": "TX-001",
        "posted_at": datetime.now().isoformat(),
        "amount": 100.00,
        "currency": "USD",
        "description": f"Payment to {vendor.name}",
    }
    transactions, _ = TransactionService.import_transactions(
        db, tenant.id, [transaction_data]
    )
    transaction = transactions[0]

    # Mock AI service to return a test explanation
    def mock_explain_match(self, invoice, transaction, score):
        return "This is a mocked AI explanation for testing purposes."

    from app.services.ai_service import AIService
    monkeypatch.setattr(AIService, "explain_match", mock_explain_match)

    # Get explanation
    response = client.get(
        f"/tenants/{tenant.id}/reconcile/explain",
        params={
            "invoice_id": invoice.id,
            "transaction_id": transaction.id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert len(data["explanation"]) > 0


def test_explain_reconciliation_fallback(client, tenant, vendor, db, monkeypatch):
    """Test AI explanation endpoint fallback when AI is unavailable."""
    from app.services.invoice_service import InvoiceService
    from app.services.transaction_service import TransactionService

    # Create invoice
    invoice = InvoiceService.create_invoice(
        db,
        tenant.id,
        Decimal("100.00"),
        vendor_id=vendor.id,
        invoice_date=datetime.now(),
        description="Office supplies",
    )

    # Create transaction
    transaction_data = {
        "external_id": "TX-001",
        "posted_at": datetime.now().isoformat(),
        "amount": 100.00,
        "currency": "USD",
        "description": f"Payment to {vendor.name}",
    }
    transactions, _ = TransactionService.import_transactions(
        db, tenant.id, [transaction_data]
    )
    transaction = transactions[0]

    # The service should fall back to deterministic explanation
    # Let's test with no API key (which triggers fallback)
    import os
    from app.services.ai_service import AIService
    
    original_key = os.environ.get("OPENAI_API_KEY")
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]

    try:
        # Reinitialize AI service without API key
        ai_service = AIService()
        explanation = ai_service.explain_match(invoice, transaction, 85.0)
        assert "explanation" in explanation.lower() or "match" in explanation.lower() or "score" in explanation.lower()
    finally:
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
