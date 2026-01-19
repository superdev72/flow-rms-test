"""Reconciliation REST endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.reconciliation_service import ReconciliationService
from app.services.ai_service import AIService
from app.schemas.reconciliation import ReconciliationResponse, ExplainResponse
from app.schemas.match import MatchResponse

router = APIRouter(prefix="/tenants/{tenant_id}/reconcile", tags=["reconciliation"])

ai_service = AIService()


@router.post("", response_model=ReconciliationResponse)
def reconcile(tenant_id: int, db: Session = Depends(get_db)):
    """Run reconciliation and return match candidates."""
    try:
        matches = ReconciliationService.reconcile(db, tenant_id)
        return ReconciliationResponse(
            matches=[MatchResponse.model_validate(m) for m in matches]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/explain", response_model=ExplainResponse)
def explain_reconciliation(
    tenant_id: int,
    invoice_id: int = Query(...),
    transaction_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Get AI explanation for a match decision."""
    from app.services.invoice_service import InvoiceService
    from app.services.transaction_service import TransactionService

    invoice = InvoiceService.get_invoice(db, tenant_id, invoice_id)
    transaction = TransactionService.get_transaction(db, tenant_id, transaction_id)

    if not invoice or not transaction:
        raise HTTPException(
            status_code=404, detail="Invoice or transaction not found"
        )

    # Calculate score
    score = float(
        ReconciliationService.calculate_match_score(invoice, transaction)
    )

    explanation = ai_service.explain_match(invoice, transaction, score)
    return ExplainResponse(explanation=explanation)


@router.post("/matches/{match_id}/confirm", response_model=MatchResponse)
def confirm_match(tenant_id: int, match_id: int, db: Session = Depends(get_db)):
    """Confirm a proposed match."""
    match = ReconciliationService.confirm_match(db, tenant_id, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found or already confirmed")
    return MatchResponse.model_validate(match)
