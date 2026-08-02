"""Unknown Contact Notification Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class UnknownRule(BaseRule):
    """Routes non-urgent messages from unverified or unknown senders (Priority: LOW)."""

    def __init__(self) -> None:
        super().__init__(name="UnknownRule", priority=RulePriority.LOW)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        is_unknown_contact = (
            "volunteer sheet" in lower_txt
            or "found your number" in lower_txt
            or (vector.new_sender and not vector.trusted_sender and not vector.personal)
        )

        if is_unknown_contact:
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="digest",
                message_type="unknown",
                reason="Non-urgent message from unknown contact routed to digest.",
                confidence=0.85,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
