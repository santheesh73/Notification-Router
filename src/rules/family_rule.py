"""Family Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class FamilyRule(BaseRule):
    """Routes messages from family members or family groups (Priority: HIGH)."""

    def __init__(self) -> None:
        super().__init__(name="FamilyRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        if vector.group_type == "Family":
            text_content = getattr(vector, "message_text", "") or ""
            lower_txt = text_content.lower()

            # Build contextual reason
            if "beta" in lower_txt or "good morning" in lower_txt:
                reason = "Known family contact sharing daily greeting or check-in."
            elif vector.trusted_sender or vector.favorite_contact:
                reason = "Personal message from trusted family member requiring attention."
            else:
                reason = "Family group message from close personal contact."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="notify",
                message_type="personal",
                reason=reason,
                confidence=0.91,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
