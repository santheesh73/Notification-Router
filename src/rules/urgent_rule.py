"""Urgent Emergency Detection Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class UrgentRule(BaseRule):
    """Detects high-priority emergencies, hospital alerts, and urgent requests (Priority: CRITICAL)."""

    def __init__(self) -> None:
        super().__init__(name="UrgentRule", priority=RulePriority.CRITICAL)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        if vector.contains_emergency or vector.contains_deadline and vector.contains_help:
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="notify",
                message_type="urgent",
                reason="Emergency signal detected requiring immediate notification.",
                confidence=0.99,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
