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
        super().__init__(name="PromotionRule", priority=RulePriority.LOW)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_promo = (
            vector.contains_discount
            or vector.contains_coupon
            or vector.contains_offer
        )

        text_content = getattr(vector, "message_text", "") or ""
        if not is_promo and text_content:
            lower_txt = str(text_content).lower()
            if any(kw in lower_txt for kw in PROMO_KEYWORDS):
                is_promo = True

        if is_promo:
            action = "mute" if vector.dismiss_rate > 0.3 else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="promotion",
                reason=f"Promotional offer routed to {action} based on heuristics.",
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
