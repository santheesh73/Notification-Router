"""Reminder Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class ReminderRule(BaseRule):
    """Routes time-sensitive reminders and deadlines (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="ReminderRule", priority=RulePriority.MEDIUM)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        if vector.contains_deadline or (vector.contains_date and vector.contains_time):
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="notify",
                message_type="reminder",
                reason="Time-sensitive deadline or reminder alert.",
                confidence=0.89,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
