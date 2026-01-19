"""GraphQL types."""
import strawberry
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.invoice import InvoiceStatus
from app.models.match import MatchStatus


@strawberry.type
class Tenant:
    """Tenant GraphQL type."""
    id: int
    name: str
    created_at: datetime


@strawberry.type
class Vendor:
    """Vendor GraphQL type."""
    id: int
    tenant_id: int
    name: str
    created_at: datetime


@strawberry.type
class Invoice:
    """Invoice GraphQL type."""
    id: int
    tenant_id: int
    vendor_id: Optional[int]
    invoice_number: Optional[str]
    amount: Decimal
    currency: str
    invoice_date: Optional[datetime]
    description: Optional[str]
    status: str  # InvoiceStatus as string
    created_at: datetime


@strawberry.type
class BankTransaction:
    """Bank transaction GraphQL type."""
    id: int
    tenant_id: int
    external_id: Optional[str]
    posted_at: datetime
    amount: Decimal
    currency: str
    description: Optional[str]
    created_at: datetime


@strawberry.type
class Match:
    """Match GraphQL type."""
    id: int
    tenant_id: int
    invoice_id: int
    bank_transaction_id: int
    score: Decimal
    status: str  # MatchStatus as string
    created_at: datetime


@strawberry.input
class TenantInput:
    """Input for creating a tenant."""
    name: str


@strawberry.input
class InvoiceInput:
    """Input for creating an invoice."""
    amount: Decimal
    currency: str = "USD"
    vendor_id: Optional[int] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    description: Optional[str] = None


@strawberry.input
class TransactionInput:
    """Input for a single transaction."""
    external_id: Optional[str] = None
    posted_at: datetime
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None


@strawberry.input
class TransactionImportInput:
    """Input for importing transactions."""
    transactions: List[TransactionInput]


@strawberry.type
class ExplainResponse:
    """Response for explanation."""
    explanation: str
