"""Payment Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class PaymentRule(BaseRule):
    """Routes payment receipts, invoices, and banking transactions (Priority: HIGH)."""

    def __init__(self) -> None:
        super().__init__(name="PaymentRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        text_lower = str(getattr(vector, "message_text", "")).lower()

        # Exclude safety advisories
        if "never ask for" in text_lower or "safety advisory" in text_lower:
            return None

        has_actual_payment = any(k in text_lower for k in ["payment", "debited", "credited", "paid", "upi", "invoice", "receipt", "transfer", "transaction"])

        is_payment = (
            vector.contains_payment
            or vector.contains_invoice
            or vector.contains_upi
            or (vector.contains_bank and (vector.contains_money or has_actual_payment))
            or vector.payments > 0
        ) and has_actual_payment

        if is_payment:
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="notify",
                message_type="payment",
                reason="Verified payment or transaction alert.",
                confidence=0.93,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
