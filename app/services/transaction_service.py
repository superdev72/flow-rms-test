"""Bank transaction service."""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.bank_transaction import BankTransaction
from app.models.tenant import Tenant
from app.models.idempotency import IdempotencyKey
import json


class TransactionService:
    """Service for bank transaction operations."""

    @staticmethod
    def import_transactions(
        db: Session,
        tenant_id: int,
        transactions: List[Dict[str, Any]],
        idempotency_key: Optional[str] = None,
    ) -> tuple[List[BankTransaction], bool]:
        """
        Import bank transactions in bulk with idempotency support.
        Returns (transactions, is_duplicate).
        """
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Check idempotency if key provided
        if idempotency_key:
            existing_key = (
                db.query(IdempotencyKey)
                .filter(
                    and_(
                        IdempotencyKey.key == idempotency_key,
                        IdempotencyKey.tenant_id == tenant_id,
                    )
                )
                .first()
            )

            if existing_key:
                # Check if payload matches
                payload_hash = IdempotencyKey.hash_payload(transactions)
                if existing_key.payload_hash == payload_hash:
                    # Same request, return cached response
                    if existing_key.response_data:
                        response_data = json.loads(existing_key.response_data)
                        transaction_ids = response_data.get("transaction_ids", [])
                        imported_transactions = (
                            db.query(BankTransaction)
                            .filter(BankTransaction.id.in_(transaction_ids))
                            .all()
                        )
                        return imported_transactions, True
                    return [], True
                else:
                    # Different payload with same key - conflict
                    raise ValueError(
                        f"Idempotency key {idempotency_key} already used with different payload"
                    )

        # Import transactions
        imported = []
        for tx_data in transactions:
            transaction = BankTransaction(
                tenant_id=tenant_id,
                external_id=tx_data.get("external_id"),
                posted_at=datetime.fromisoformat(tx_data["posted_at"])
                if isinstance(tx_data.get("posted_at"), str)
                else tx_data.get("posted_at"),
                amount=Decimal(str(tx_data["amount"])),
                currency=tx_data.get("currency", "USD"),
                description=tx_data.get("description"),
            )
            db.add(transaction)
            imported.append(transaction)

        db.flush()  # Get IDs

        # Store idempotency key if provided
        if idempotency_key:
            payload_hash = IdempotencyKey.hash_payload(transactions)
            response_data = json.dumps({"transaction_ids": [t.id for t in imported]})
            idempotency_record = IdempotencyKey(
                key=idempotency_key,
                tenant_id=tenant_id,
                payload_hash=payload_hash,
                response_data=response_data,
            )
            db.add(idempotency_record)

        db.commit()

        # Refresh to get all fields
        for transaction in imported:
            db.refresh(transaction)

        return imported, False

    @staticmethod
    def get_transaction(
        db: Session, tenant_id: int, transaction_id: int
    ) -> Optional[BankTransaction]:
        """Get a transaction by ID, ensuring tenant isolation."""
        return (
            db.query(BankTransaction)
            .filter(
                and_(
                    BankTransaction.id == transaction_id,
                    BankTransaction.tenant_id == tenant_id,
                )
            )
            .first()
        )

    @staticmethod
    def list_transactions(
        db: Session,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BankTransaction]:
        """List transactions, ensuring tenant isolation."""
        return (
            db.query(BankTransaction)
            .filter(BankTransaction.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
