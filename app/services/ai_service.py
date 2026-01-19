"""AI service for explanations."""
import os
from typing import Optional
from openai import OpenAI
from app.models.invoice import Invoice
from app.models.bank_transaction import BankTransaction


class AIService:
    """Service for AI-powered explanations."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def explain_match(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: float,
    ) -> str:
        """
        Generate an AI explanation for a match.
        Falls back to deterministic explanation if AI is unavailable.
        """
        if not self.client:
            return self._fallback_explanation(invoice, transaction, score)

        try:
            prompt = self._build_prompt(invoice, transaction, score)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial reconciliation assistant. Provide brief, clear explanations (2-6 sentences) about why an invoice and bank transaction likely match.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                timeout=10,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # Fallback on any error
            return self._fallback_explanation(invoice, transaction, score)

    def _build_prompt(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: float,
    ) -> str:
        """Build the prompt for AI explanation."""
        prompt_parts = [
            f"Invoice Details:",
            f"- Amount: {invoice.amount} {invoice.currency}",
            f"- Date: {invoice.invoice_date}",
            f"- Description: {invoice.description or 'N/A'}",
        ]

        if invoice.vendor:
            prompt_parts.append(f"- Vendor: {invoice.vendor.name}")

        prompt_parts.extend(
            [
                f"\nBank Transaction Details:",
                f"- Amount: {transaction.amount} {transaction.currency}",
                f"- Date: {transaction.posted_at}",
                f"- Description: {transaction.description or 'N/A'}",
                f"\nMatch Score: {score}/100",
                "\nExplain why these likely match:",
            ]
        )

        return "\n".join(prompt_parts)

    def _fallback_explanation(
        self,
        invoice: Invoice,
        transaction: BankTransaction,
        score: float,
    ) -> str:
        """Generate a deterministic fallback explanation."""
        reasons = []

        # Amount match
        if invoice.amount == transaction.amount:
            reasons.append("exact amount match")
        elif abs(invoice.amount - transaction.amount) / invoice.amount <= 0.01:
            reasons.append("amount within 1% tolerance")

        # Date proximity
        if invoice.invoice_date and transaction.posted_at:
            days_diff = abs((invoice.invoice_date - transaction.posted_at).days)
            if days_diff == 0:
                reasons.append("same date")
            elif days_diff <= 3:
                reasons.append(f"dates within {days_diff} days")

        # Text similarity
        if invoice.description and transaction.description:
            from difflib import SequenceMatcher

            similarity = SequenceMatcher(
                None, invoice.description.lower(), transaction.description.lower()
            ).ratio()
            if similarity > 0.5:
                reasons.append("similar descriptions")

        # Vendor name
        if invoice.vendor and transaction.description:
            if invoice.vendor.name.lower() in transaction.description.lower():
                reasons.append("vendor name appears in transaction")

        if reasons:
            explanation = f"This match (score: {score:.1f}/100) is suggested because of: {', '.join(reasons)}."
        else:
            explanation = f"This match (score: {score:.1f}/100) is suggested based on partial matching criteria."

        return explanation
