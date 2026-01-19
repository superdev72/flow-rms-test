"""Match schemas."""
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.models.match import MatchStatus


class MatchResponse(BaseModel):
    """Schema for match response."""
    id: int
    tenant_id: int
    invoice_id: int
    bank_transaction_id: int
    score: Decimal
    status: MatchStatus
    created_at: datetime

    class Config:
        from_attributes = True


class MatchConfirm(BaseModel):
    """Schema for confirming a match."""
    pass  # No additional fields needed
