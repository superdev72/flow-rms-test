"""Reconciliation schemas."""
from pydantic import BaseModel
from typing import List
from app.schemas.match import MatchResponse


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response."""
    matches: List[MatchResponse]


class ExplainResponse(BaseModel):
    """Schema for explanation response."""
    explanation: str
