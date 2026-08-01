"""Business Update Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult

BUSINESS_KEYWORDS = {
    "dear customer",
    "delivery attempt",
    "pickup today",
    "order ending",
    "health-related update",
    "account notice",
    "fedex",
    "shopee",
    "shipped",
    "delivered",
    "tracking",
    "invoice",
    "receipts",
}


class BusinessRule(BaseRule):
    """Routes operational business updates like shipping, deliveries, and bookings (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="BusinessRule", priority=RulePriority.MEDIUM)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_bus = (
            vector.business
            or vector.trusted_business
            or vector.orders > 0
            or vector.bookings > 0
        )

        text_content = getattr(vector, "message_text", "") or ""
        if not is_bus and text_content:
            lower_txt = str(text_content).lower()
            if any(kw in lower_txt for kw in BUSINESS_KEYWORDS):
                is_bus = True

        if is_bus:
            action = "notify" if (vector.orders > 0 or vector.contains_deadline or vector.contains_time or "shipped" in text_content.lower() or "delivered" in text_content.lower()) else "digest"

            # Build contextual reason
            if vector.trusted_business or vector.verified:
                reason = f"Verified business update from trusted service provider."
            elif "delivery" in text_content.lower() or "shipped" in text_content.lower() or "order" in text_content.lower():
                reason = f"Order or delivery status update from business channel."
            elif "health" in text_content.lower() or "appointment" in text_content.lower():
                reason = f"Health or appointment update from service provider."
            elif vector.orders > 0:
                reason = f"Business notification related to active order history."
            else:
                reason = f"Business operational update routed to {action}."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="business_update",
                reason=reason,
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
