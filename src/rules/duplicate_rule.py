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
            text_content = str(getattr(vector, "message_text", "") or "")
            lower_txt = text_content.lower()
            is_spam = any(kw in lower_txt for kw in ["offer", "discount", "deal", "sale", "buy", "price", "plot", "token"])

            # Determine message type for muted duplicate
            if any(kw in lower_txt for kw in ["good morning", "good evening", "stay positive", "keep smiling", "blessings"]):
                msg_type = "greeting"
                reason = "Forwarded greeting chain message muted to reduce notification clutter."
            elif is_spam or any(kw in lower_txt for kw in ["photos for"]):
                msg_type = "promotion"
                reason = "Repeated promotional broadcast message previously dismissed by users."
            else:
                msg_type = "forward"
                reason = "Forwarded chain message detected with high distribution count."

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
