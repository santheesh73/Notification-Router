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
    "clearance",
    "special price",
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
            utility_score = self._calculate_promotion_utility_score(vector, lower_txt)

            # Step 3: Compute Action Scores (Highest score wins)
            digest_score = utility_score
            mute_score = 1.0 - utility_score

            if digest_score >= mute_score:
                action = "digest"
                reason = "Useful or relevant promotional message routed to digest."
            else:
                action = "mute"
                reason = "Low utility or unsolicited promotional broadcast muted."

            margin = abs(digest_score - mute_score)
            calibrated_conf = round(min(0.95, max(0.68, 0.72 + 0.25 * margin)), 2)

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="promotion",
                reason=reason,
                confidence=calibrated_conf,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None

    def _calculate_promotion_utility_score(self, vector: FeatureVector, lower_txt: str) -> float:
        """Compute weighted Promotion Utility Score in range [0.0, 1.0] using generalized domain features."""
        # Baseline score: 0.60 (legitimate non-spam promotion defaults to digest)
        base_score = 0.60

        # Positive Signals (Trust, Commerce & Interactivity)
        pos_signal = 0.0
        if vector.verified or vector.trusted_business:
            pos_signal += 0.10
        if vector.favorite_business:
            pos_signal += 0.10
        if vector.orders > 0 or vector.payments > 0 or vector.bookings > 0:
            pos_signal += 0.10
        if vector.reply_history > 0 or vector.interaction_count > 0 or getattr(vector, "user_participation", 0) > 0:
            pos_signal += 0.10
        if vector.contains_coupon or vector.contains_discount:
            pos_signal += 0.05

        # Negative Spam Penalties
        neg_penalty = 0.0
        if vector.dismiss_rate > 0.4:
            neg_penalty += vector.dismiss_rate * 0.30

        if vector.report_history > 0 or getattr(vector, "report_rate", 0.0) > 0.0:
            neg_penalty += 0.30

        if getattr(vector, "risk_score", 0.0) > 0.2:
            neg_penalty += getattr(vector, "risk_score", 0.0) * 0.30

        if vector.forwarded_count > 2 or getattr(vector, "duplicate_probability", 0.0) > 0.5:
            neg_penalty += 0.25

        # Multiple Spam Signals Penalty: Require multiple simultaneous spam signals to suppress to mute
        spam_signal_count = (
            (1 if vector.dismiss_rate > 0.4 else 0)
            + (1 if vector.report_history > 0 or getattr(vector, "report_rate", 0.0) > 0.0 else 0)
            + (1 if getattr(vector, "risk_score", 0.0) > 0.2 else 0)
            + (1 if vector.forwarded_count > 2 or getattr(vector, "duplicate_probability", 0.0) > 0.5 else 0)
        )
        if spam_signal_count >= 2:
            neg_penalty += 0.25

        utility = base_score + pos_signal - neg_penalty
        return max(0.0, min(1.0, utility))


