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

        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        is_biz_salutation = any(k in lower_txt for k in ["hi customer", "dear customer", "team amazon", "pvr cinemas", "safety advisory"])
        is_order_delivery = any(kw in lower_txt for kw in ["order ending", "order packed", "delivery attempt", "pickup today", "shipped", "delivered", "tracking", "local hub"])
        is_operational_biz = is_biz_salutation or any(kw in lower_txt for kw in ["feedback", "invoice", "receipt"])

        # Phase 7 Restriction: Do NOT classify events, promotions, greetings, or personal as business_update unless formal business salutation/order exists
        ev_score = getattr(vector, "event_score", 0)
        promo_score = getattr(vector, "promotion_score", 0)

        if not is_biz_salutation and not is_order_delivery and (ev_score > 0 or promo_score > 0 or any(k in lower_txt for k in ["reply stop", "per person", "nights", "selling", "kurta set"])):
            return None

        # Step 3 Requirement: Personal contacts (u_...) must NOT be classified as business_update unless formal business salutation or order delivery exists
        if vector.sender_id.startswith("u_") and not is_biz_salutation and not is_order_delivery:
            return None

        is_bus = (
            (vector.business_id and (vector.trusted_business or vector.verified))
            or is_order_delivery
            or is_biz_salutation
        )

        if is_bus:
            action = "notify" if (is_order_delivery or "order ending" in lower_txt or "packed" in lower_txt) else "digest"

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
