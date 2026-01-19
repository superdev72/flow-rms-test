"""Match model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class MatchStatus(str, enum.Enum):
    """Match status enumeration."""
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Match(Base):
    """Match model representing a match between invoice and bank transaction."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    bank_transaction_id = Column(Integer, ForeignKey("bank_transactions.id"), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    status = Column(Enum(MatchStatus), default=MatchStatus.PROPOSED, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="matches")
    invoice = relationship("Invoice", back_populates="matches")
    bank_transaction = relationship("BankTransaction", back_populates="matches")
