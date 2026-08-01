"""Event & Schedule Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class EventRule(BaseRule):
    """Routes events, meetings, exams, and workshops (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="EventRule", priority=RulePriority.MEDIUM)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_event = (
            vector.contains_meeting
            or vector.contains_exam
            or vector.contains_assignment
            or vector.contains_event
        )

        if is_event:
            action = "notify" if vector.contains_deadline else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="event",
                reason=f"Scheduled event or meeting notice routed to {action}.",
                confidence=0.85,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
