"""Bank transaction schemas."""
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any


class TransactionCreate(BaseModel):
    """Schema for a single transaction."""
    external_id: Optional[str] = None
    posted_at: datetime
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None


class TransactionImport(BaseModel):
    """Schema for importing transactions."""
    transactions: List[TransactionCreate]


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    tenant_id: int
    external_id: Optional[str]
    posted_at: datetime
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
