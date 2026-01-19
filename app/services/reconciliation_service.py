"""Reconciliation service."""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from app.models.invoice import Invoice, InvoiceStatus
from app.models.bank_transaction import BankTransaction
from app.models.match import Match, MatchStatus
from app.models.tenant import Tenant


class ReconciliationService:
    """Service for reconciliation operations."""

    @staticmethod
    def calculate_match_score(
        invoice: Invoice, transaction: BankTransaction
    ) -> Decimal:
        """
        Calculate a match score between 0 and 100.
        Scoring algorithm:
        - Exact amount match: 40 points
        - Amount within 1% tolerance: 30 points
        - Date proximity (within 3 days): 20 points
        - Text similarity (description): 20 points
        - Vendor name in transaction description: 10 points (bonus)
        """
        score = Decimal("0.0")

        # Amount matching (40 points max)
        if invoice.amount == transaction.amount:
            score += Decimal("40.0")
        elif invoice.amount > 0:
            tolerance = abs(invoice.amount - transaction.amount) / invoice.amount
            if tolerance <= Decimal("0.01"):  # Within 1%
                score += Decimal("30.0")
            elif tolerance <= Decimal("0.05"):  # Within 5%
                score += Decimal("15.0")

        # Date proximity (20 points max)
        if invoice.invoice_date and transaction.posted_at:
            date_diff = abs((invoice.invoice_date - transaction.posted_at).days)
            if date_diff == 0:
                score += Decimal("20.0")
            elif date_diff <= 1:
                score += Decimal("15.0")
            elif date_diff <= 3:
                score += Decimal("10.0")
            elif date_diff <= 7:
                score += Decimal("5.0")

        # Text similarity (20 points max)
        if invoice.description and transaction.description:
            similarity = SequenceMatcher(
                None,
                invoice.description.lower(),
                transaction.description.lower(),
            ).ratio()
            score += Decimal(str(similarity * 20))

        # Vendor name bonus (10 points max)
        if invoice.vendor and transaction.description:
            vendor_name_lower = invoice.vendor.name.lower()
            desc_lower = transaction.description.lower()
            if vendor_name_lower in desc_lower:
                score += Decimal("10.0")

        return min(score, Decimal("100.0"))

    @staticmethod
    def reconcile(
        db: Session, tenant_id: int
    ) -> List[Match]:
        """
        Run reconciliation and create match candidates.
        Returns best matches per invoice (one match per invoice).
        """
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Get open invoices
        open_invoices = (
            db.query(Invoice)
            .filter(
                and_(
                    Invoice.tenant_id == tenant_id,
                    Invoice.status == InvoiceStatus.OPEN,
                )
            )
            .all()
        )

        # Get unmatched transactions (not confirmed in any match)
        matched_transaction_ids_subq = (
            db.query(Match.bank_transaction_id)
            .filter(
                and_(
                    Match.tenant_id == tenant_id,
                    Match.status == MatchStatus.CONFIRMED,
                )
            )
            .subquery()
        )

        unmatched_transactions = (
            db.query(BankTransaction)
            .filter(
                and_(
                    BankTransaction.tenant_id == tenant_id,
                    ~BankTransaction.id.in_(
                        db.query(matched_transaction_ids_subq.c.bank_transaction_id)
                    ),
                )
            )
            .all()
        )

        # Calculate scores and create matches
        matches = []
        for invoice in open_invoices:
            best_match = None
            best_score = Decimal("0.0")

            for transaction in unmatched_transactions:
                # Skip if already matched to this invoice
                existing_match = (
                    db.query(Match)
                    .filter(
                        and_(
                            Match.invoice_id == invoice.id,
                            Match.bank_transaction_id == transaction.id,
                            Match.tenant_id == tenant_id,
                        )
                    )
                    .first()
                )
                if existing_match:
                    continue

                score = ReconciliationService.calculate_match_score(
                    invoice, transaction
                )

                if score > best_score and score >= Decimal("30.0"):  # Minimum threshold
                    best_score = score
                    best_match = transaction

            if best_match:
                match = Match(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    bank_transaction_id=best_match.id,
                    score=best_score,
                    status=MatchStatus.PROPOSED,
                )
                db.add(match)
                matches.append(match)

        db.commit()

        # Refresh matches
        for match in matches:
            db.refresh(match)

        return matches

    @staticmethod
    def confirm_match(
        db: Session, tenant_id: int, match_id: int
    ) -> Optional[Match]:
        """Confirm a proposed match."""
        match = (
            db.query(Match)
            .filter(
                and_(
                    Match.id == match_id,
                    Match.tenant_id == tenant_id,
                    Match.status == MatchStatus.PROPOSED,
                )
            )
            .first()
        )

        if not match:
            return None

        # Update match status
        match.status = MatchStatus.CONFIRMED

        # Update invoice status
        invoice = match.invoice
        invoice.status = InvoiceStatus.MATCHED

        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def get_match(
        db: Session, tenant_id: int, match_id: int
    ) -> Optional[Match]:
        """Get a match by ID, ensuring tenant isolation."""
        return (
            db.query(Match)
            .filter(
                and_(Match.id == match_id, Match.tenant_id == tenant_id)
            )
            .first()
        )

    @staticmethod
    def list_matches(
        db: Session,
        tenant_id: int,
        status: Optional[MatchStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Match]:
        """List matches, ensuring tenant isolation."""
        query = db.query(Match).filter(Match.tenant_id == tenant_id)

        if status:
            query = query.filter(Match.status == status)

        return query.offset(skip).limit(limit).all()
