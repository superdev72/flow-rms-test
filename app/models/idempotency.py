"""Idempotency key model."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base
import hashlib
import json


class IdempotencyKey(Base):
    """Idempotency key model for tracking idempotent requests."""
    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    payload_hash = Column(String, nullable=False)  # Hash of the request payload
    response_data = Column(Text, nullable=True)  # JSON string of response
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @staticmethod
    def hash_payload(payload: dict) -> str:
        """Generate a hash of the payload for comparison."""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()
