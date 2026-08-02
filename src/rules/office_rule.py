"""Office, Work & Group Announcement Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult

GROUP_ANNOUNCEMENT_KEYWORDS = {
    "maintenance",
    "gate",
    "tanker",
    "flat",
    "potluck",
    "society",
    "slides",
    "circular",
    "school",
    "match",
    "fee receipt",
    "rollback",
    "system note",
    "internal router metadata",
    "admin notice",
    "office",
}


class OfficeRule(BaseRule):
    """Routes messages from official work groups, managers, and team leads (Priority: HIGH)."""

    def __init__(self) -> None:
        super().__init__(name="OfficeRule", priority=RulePriority.LOW)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_office_or_group = (
            vector.group_type in ["Office", "School", "Apartment", "Sports"]
            or vector.group
            or vector.trusted_group
        )

        text_content = getattr(vector, "message_text", "") or ""
        if not is_office_or_group and text_content:
            lower_txt = str(text_content).lower()
            if any(kw in lower_txt for kw in GROUP_ANNOUNCEMENT_KEYWORDS):
                is_office_or_group = True

        if is_office_or_group:
            action = "notify" if (vector.contains_deadline or vector.contains_emergency or "urgent" in text_content.lower() or "alert" in text_content.lower() or "admin notice" in text_content.lower()) else "digest"

            # Build contextual reason
            group_name = vector.group_type if vector.group_type != "Other" else "work"
            if vector.trusted_group:
                reason = f"Trusted {group_name.lower()} group announcement routed to {action}."
            elif "maintenance" in text_content.lower() or "tanker" in text_content.lower() or "gate" in text_content.lower():
                reason = f"Society or apartment facility update requiring attention."
            elif "school" in text_content.lower() or "circular" in text_content.lower():
                reason = f"School or academic notification from group channel."
            elif "rollback" in text_content.lower() or "deployment" in text_content.lower():
                reason = f"Work deployment or technical update from team channel."
            else:
                reason = f"Group or organizational update from {group_name.lower()} channel."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="business_update",
                reason=reason,
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
