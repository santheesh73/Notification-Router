"""Duplicate Message Detection Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class DuplicateRule(BaseRule):
    """Mutes duplicate broadcast messages received repeatedly (Priority: HIGH)."""

    def __init__(self) -> None:
        super().__init__(name="DuplicateRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        # Check for high repeat frequency or duplicate message indicators
        if vector.forwarded_count >= 5 and not vector.trusted_sender:
            text_content = getattr(vector, "message_text", "") or ""
            lower_txt = text_content.lower()

            # Determine if it's spam (promotional) or forward (chain message)
            is_spam = any(kw in lower_txt for kw in ["offer", "discount", "deal", "sale", "buy", "price", "plot", "token"])

            if is_spam:
                msg_type = "spam"
                reason = "Repeated promotional broadcast message previously dismissed by users."
            elif "forward" in lower_txt or "share" in lower_txt or "bless" in lower_txt or "send this" in lower_txt:
                msg_type = "forward"
                reason = "Forwarded chain message detected with high forward count."
            elif vector.forwarded_count >= 7:
                msg_type = "spam"
                reason = "Mass-forwarded broadcast with excessive distribution count."
            else:
                msg_type = "forward"
                reason = "Duplicate broadcast content forwarded across multiple groups."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="mute",
                message_type=msg_type,
                reason=reason,
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
