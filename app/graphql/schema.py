"""GraphQL schema."""
import strawberry
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.tenant_service import TenantService
from app.services.invoice_service import InvoiceService
from app.services.transaction_service import TransactionService
from app.services.reconciliation_service import ReconciliationService
from app.services.ai_service import AIService
from app.models.invoice import InvoiceStatus
from app.models.match import MatchStatus
from app.graphql.types import (
    Tenant,
    Invoice,
    BankTransaction,
    Match,
    TenantInput,
    InvoiceInput,
    TransactionImportInput,
    ExplainResponse,
)


def get_db_session() -> Session:
    """Get database session for GraphQL."""
    # Create a new session for GraphQL requests
    # Note: In production, you'd want to use dependency injection or context
    from app.database import SessionLocal
    return SessionLocal()


ai_service = AIService()


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    def tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """Get all tenants."""
        db = get_db_session()
        try:
            tenants = TenantService.list_tenants(db, skip=skip, limit=limit)
            return [
                Tenant(
                    id=t.id,
                    name=t.name,
                    created_at=t.created_at,
                )
                for t in tenants
            ]
        finally:
            db.close()

    @strawberry.field
    def invoices(
        self,
        tenant_id: int,
        status: Optional[str] = None,
        vendor_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Invoice]:
        """Get invoices for a tenant."""
        db = get_db_session()
        try:
            invoice_status = InvoiceStatus(status) if status else None
            invoices = InvoiceService.list_invoices(
                db,
                tenant_id,
                status=invoice_status,
                vendor_id=vendor_id,
                skip=skip,
                limit=limit,
            )
            return [
                Invoice(
                    id=i.id,
                    tenant_id=i.tenant_id,
                    vendor_id=i.vendor_id,
                    invoice_number=i.invoice_number,
                    amount=i.amount,
                    currency=i.currency,
                    invoice_date=i.invoice_date,
                    description=i.description,
                    status=i.status.value,
                    created_at=i.created_at,
                )
                for i in invoices
            ]
        finally:
            db.close()

    @strawberry.field
    def bank_transactions(
        self, tenant_id: int, skip: int = 0, limit: int = 100
    ) -> List[BankTransaction]:
        """Get bank transactions for a tenant."""
        db = get_db_session()
        try:
            transactions = TransactionService.list_transactions(
                db, tenant_id, skip=skip, limit=limit
            )
            return [
                BankTransaction(
                    id=t.id,
                    tenant_id=t.tenant_id,
                    external_id=t.external_id,
                    posted_at=t.posted_at,
                    amount=t.amount,
                    currency=t.currency,
                    description=t.description,
                    created_at=t.created_at,
                )
                for t in transactions
            ]
        finally:
            db.close()

    @strawberry.field
    def match_candidates(
        self, tenant_id: int, status: Optional[str] = None
    ) -> List[Match]:
        """Get match candidates for a tenant."""
        db = get_db_session()
        try:
            match_status = MatchStatus(status) if status else None
            matches = ReconciliationService.list_matches(
                db, tenant_id, status=match_status
            )
            return [
                Match(
                    id=m.id,
                    tenant_id=m.tenant_id,
                    invoice_id=m.invoice_id,
                    bank_transaction_id=m.bank_transaction_id,
                    score=m.score,
                    status=m.status.value,
                    created_at=m.created_at,
                )
                for m in matches
            ]
        finally:
            db.close()

    @strawberry.field
    def explain_reconciliation(
        self, tenant_id: int, invoice_id: int, transaction_id: int
    ) -> ExplainResponse:
        """Get AI explanation for a match decision."""
        db = get_db_session()
        try:
            invoice = InvoiceService.get_invoice(db, tenant_id, invoice_id)
            transaction = TransactionService.get_transaction(db, tenant_id, transaction_id)

            if not invoice or not transaction:
                raise ValueError("Invoice or transaction not found")

            score = float(ReconciliationService.calculate_match_score(invoice, transaction))
            explanation = ai_service.explain_match(invoice, transaction, score)

            return ExplainResponse(explanation=explanation)
        finally:
            db.close()


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    @strawberry.mutation
    def create_tenant(self, input: TenantInput) -> Tenant:
        """Create a new tenant."""
        db = get_db_session()
        try:
            tenant = TenantService.create_tenant(db, input.name)
            return Tenant(
                id=tenant.id,
                name=tenant.name,
                created_at=tenant.created_at,
            )
        finally:
            db.close()

    @strawberry.mutation
    def create_invoice(self, tenant_id: int, input: InvoiceInput) -> Invoice:
        """Create a new invoice."""
        db = get_db_session()
        try:
            invoice = InvoiceService.create_invoice(
                db,
                tenant_id,
                input.amount,
                input.currency,
                input.vendor_id,
                input.invoice_number,
                input.invoice_date,
                input.description,
            )
            return Invoice(
                id=invoice.id,
                tenant_id=invoice.tenant_id,
                vendor_id=invoice.vendor_id,
                invoice_number=invoice.invoice_number,
                amount=invoice.amount,
                currency=invoice.currency,
                invoice_date=invoice.invoice_date,
                description=invoice.description,
                status=invoice.status.value,
                created_at=invoice.created_at,
            )
        except ValueError as e:
            raise ValueError(str(e))
        finally:
            db.close()

    @strawberry.mutation
    def delete_invoice(self, tenant_id: int, invoice_id: int) -> bool:
        """Delete an invoice."""
        db = get_db_session()
        try:
            success = InvoiceService.delete_invoice(db, tenant_id, invoice_id)
            if not success:
                raise ValueError("Invoice not found")
            return True
        finally:
            db.close()

    @strawberry.mutation
    def import_bank_transactions(
        self,
        tenant_id: int,
        input: TransactionImportInput,
        idempotency_key: Optional[str] = None,
    ) -> List[BankTransaction]:
        """Import bank transactions."""
        db = get_db_session()
        try:
            transactions_data = [
                {
                    "external_id": tx.external_id,
                    "posted_at": tx.posted_at.isoformat() if tx.posted_at else None,
                    "amount": float(tx.amount),
                    "currency": tx.currency,
                    "description": tx.description,
                }
                for tx in input.transactions
            ]

            imported, _ = TransactionService.import_transactions(
                db, tenant_id, transactions_data, idempotency_key
            )

            return [
                BankTransaction(
                    id=t.id,
                    tenant_id=t.tenant_id,
                    external_id=t.external_id,
                    posted_at=t.posted_at,
                    amount=t.amount,
                    currency=t.currency,
                    description=t.description,
                    created_at=t.created_at,
                )
                for t in imported
            ]
        except ValueError as e:
            raise ValueError(str(e))
        finally:
            db.close()

    @strawberry.mutation
    def reconcile(self, tenant_id: int) -> List[Match]:
        """Run reconciliation."""
        db = get_db_session()
        try:
            matches = ReconciliationService.reconcile(db, tenant_id)
            return [
                Match(
                    id=m.id,
                    tenant_id=m.tenant_id,
                    invoice_id=m.invoice_id,
                    bank_transaction_id=m.bank_transaction_id,
                    score=m.score,
                    status=m.status.value,
                    created_at=m.created_at,
                )
                for m in matches
            ]
        except ValueError as e:
            raise ValueError(str(e))
        finally:
            db.close()

    @strawberry.mutation
    def confirm_match(self, tenant_id: int, match_id: int) -> Match:
        """Confirm a match."""
        db = get_db_session()
        try:
            match = ReconciliationService.confirm_match(db, tenant_id, match_id)
            if not match:
                raise ValueError("Match not found or already confirmed")
            return Match(
                id=match.id,
                tenant_id=match.tenant_id,
                invoice_id=match.invoice_id,
                bank_transaction_id=match.bank_transaction_id,
                score=match.score,
                status=match.status.value,
                created_at=match.created_at,
            )
        finally:
            db.close()


schema = strawberry.Schema(query=Query, mutation=Mutation)
