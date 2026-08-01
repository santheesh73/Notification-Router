"""Personal Direct Message Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class PersonalRule(BaseRule):
    """Routes direct messages from trusted or favorite personal contacts (Priority: MEDIUM)."""

    def __init__(self) -> None:
        super().__init__(name="PersonalRule", priority=RulePriority.MEDIUM)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        # Route only if contact is trusted, favorite, has reply history, or asks a direct question/deadline
        if (vector.personal or vector.conversation_type == "personal") and (
            vector.trusted_sender or vector.favorite_contact or vector.reply_rate > 0.1 or vector.contains_question or vector.contains_deadline
        ):
            action = "notify" if (vector.favorite_contact or vector.trusted_sender or vector.contains_question or vector.contains_deadline) else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="personal",
                reason=f"Direct personal message from trusted contact routed to {action}.",
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
