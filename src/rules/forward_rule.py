"""Forwarded Message Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class ForwardRule(BaseRule):
    """Routes forwarded broadcast messages to daily digest (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="ForwardRule", priority=RulePriority.MEDIUM)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        if vector.is_forwarded or vector.forwarded_count >= 1:
            text_content = getattr(vector, "message_text", "") or ""
            lower_txt = text_content.lower()

            if "blessing" in lower_txt or "share this" in lower_txt or "forward" in lower_txt:
                reason = "Forwarded chain message with social sharing pattern."
            elif "health" in lower_txt or "secret" in lower_txt:
                reason = "Forwarded health misinformation or unverified claim."
            elif vector.forwarded_count >= 3:
                reason = f"Widely forwarded broadcast message ({vector.forwarded_count}x forward count)."
            else:
                reason = "Forwarded content from external source routed to digest."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="digest",
                message_type="forward",
                reason=reason,
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
