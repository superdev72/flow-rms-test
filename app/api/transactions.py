"""Bank transaction REST endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionImport, TransactionResponse

router = APIRouter(
    prefix="/tenants/{tenant_id}/bank-transactions", tags=["bank-transactions"]
)


@router.post("/import", response_model=List[TransactionResponse], status_code=201)
def import_transactions(
    tenant_id: int,
    transaction_import: TransactionImport,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """Import bank transactions in bulk with idempotency support."""
    try:
        transactions_data = [
            {
                "external_id": tx.external_id,
                "posted_at": tx.posted_at.isoformat() if tx.posted_at else None,
                "amount": float(tx.amount),
                "currency": tx.currency,
                "description": tx.description,
            }
            for tx in transaction_import.transactions
        ]

        imported, is_duplicate = TransactionService.import_transactions(
            db, tenant_id, transactions_data, idempotency_key
        )

        return imported
    except ValueError as e:
        if "already used with different payload" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
