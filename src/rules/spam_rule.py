"""Spam Detection Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class SpamRule(BaseRule):
    """Detects repeated ignored or reported spam senders (Priority: HIGH)."""

    def __init__(self) -> None:
        super().__init__(name="SpamRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_spam = vector.report_history > 0 or vector.blocked_history or vector.report_rate > 0.3

        if is_spam:
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="mute",
                message_type="spam",
                reason="Sender has a history of reported spam.",
                confidence=0.94,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
