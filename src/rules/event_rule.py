"""Event & Schedule Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class EventRule(BaseRule):
    """Routes events, meetings, exams, and workshops (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="EventRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        # Exclude casual personal chat, safety advisories, or volunteer registrations
        if any(k in lower_txt for k in ["talk tomorrow", "sunday pickup", "safety advisory", "volunteer sheet"]):
            return None

        ev_score = getattr(vector, "event_score", 0)
        is_event = (
            ev_score > 0
            or vector.contains_meeting
            or vector.contains_exam
            or vector.contains_assignment
            or vector.contains_event
            or any(k in lower_txt for k in ["cultural night", "form is open", "add flat no", "dish in the sheet"])
        )

        if is_event:
            txt_lower = str(getattr(vector, "message_text", "")).lower()
            is_time_critical = any(k in txt_lower for k in ["bus is leaving", "early", "kids down by", "appointment", "consent note", "school circular"]) or vector.contains_deadline
            action = "notify" if is_time_critical else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="event",
                reason=f"Scheduled event or meeting notice routed to {action}.",
                confidence=0.88,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
