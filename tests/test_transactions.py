"""Tests for bank transaction endpoints."""
import pytest
from datetime import datetime


def test_import_transactions(client, tenant):
    """Test importing bank transactions."""
    transactions = [
        {
            "external_id": "TX-001",
            "posted_at": datetime.now().isoformat(),
            "amount": "100.00",
            "currency": "USD",
            "description": "Payment for invoice",
        },
        {
            "external_id": "TX-002",
            "posted_at": datetime.now().isoformat(),
            "amount": "200.00",
            "currency": "USD",
            "description": "Another payment",
        },
    ]

    response = client.post(
        f"/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
        headers={"Idempotency-Key": "test-key-1"},
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["external_id"] == "TX-001"
    assert data[1]["external_id"] == "TX-002"


def test_import_transactions_idempotency(client, tenant):
    """Test idempotency for transaction imports."""
    transactions = [
        {
            "external_id": "TX-001",
            "posted_at": datetime.now().isoformat(),
            "amount": "100.00",
            "currency": "USD",
            "description": "Payment",
        },
    ]

    # First import
    response1 = client.post(
        f"/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
        headers={"Idempotency-Key": "idempotent-key-1"},
    )
    assert response1.status_code == 201
    transaction_ids_1 = [t["id"] for t in response1.json()]

    # Second import with same key and payload (should return same result)
    response2 = client.post(
        f"/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": transactions},
        headers={"Idempotency-Key": "idempotent-key-1"},
    )
    assert response2.status_code == 201
    transaction_ids_2 = [t["id"] for t in response2.json()]
    assert transaction_ids_1 == transaction_ids_2

    # Third import with same key but different payload (should fail)
    different_transactions = [
        {
            "external_id": "TX-002",
            "posted_at": datetime.now().isoformat(),
            "amount": "200.00",
            "currency": "USD",
            "description": "Different payment",
        },
    ]
    response3 = client.post(
        f"/tenants/{tenant.id}/bank-transactions/import",
        json={"transactions": different_transactions},
        headers={"Idempotency-Key": "idempotent-key-1"},
    )
    assert response3.status_code == 409
