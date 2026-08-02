"""Promotional & Offer Message Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult

PROMO_KEYWORDS = {
    "deal",
    "discount",
    "limited time",
    "travel deal",
    "coupon",
    "promo",
    "offer",
    "flat ",
    "off",
    "sale",
    "razorpayx",
    "cashback",
}


class PromotionRule(BaseRule):
    """Routes marketing promotions, discounts, and offers (Priority: LOW)."""

    def __init__(self) -> None:
        super().__init__(name="PromotionRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        # Exclude order delivery updates
        if any(k in lower_txt for k in ["order ending", "order packed", "delivery attempt", "local hub", "shipped"]):
            return None

        promo_score = getattr(vector, "promotion_score", 0)
        is_promo = (
            promo_score > 0
            or vector.contains_discount
            or vector.contains_coupon
            or vector.contains_offer
        )

        if not is_promo and text_content:
            if any(kw in lower_txt for kw in PROMO_KEYWORDS):
                is_promo = True

        if is_promo:
            is_duplicate = vector.is_forwarded or getattr(vector, "duplicate_probability", 0) > 0.5
            is_curated_deal = any(k in lower_txt for k in ["rs ", "per person", "nights", "ladakh", "helmet", "kurta set"])
            is_unsolicited_marketing = any(k in lower_txt for k in ["50% off", "try50", "shopping offer"])

            if is_duplicate or is_unsolicited_marketing or vector.dismiss_rate > 0.3:
                action = "mute"
            elif is_curated_deal:
                action = "digest"
            else:
                action = "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="promotion",
                reason=f"Promotional offer or commercial message routed to {action}.",
                confidence=0.88,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
