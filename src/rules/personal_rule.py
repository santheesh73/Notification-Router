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

        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        # Exclude business messages, order delivery, unknown sender registrations, or unknown/new senders
        is_order_deliv = any(k in lower_txt for k in ["order ending", "order packed", "delivery attempt", "local hub", "shipped"])
        if vector.business_id or vector.trusted_business or is_order_deliv or "volunteer sheet" in lower_txt or vector.new_sender or vector.sender_id in ["USR_999", "USR_UNKNOWN"]:
            return None

        is_personal_chat = (
            vector.personal
            or vector.conversation_type == "personal"
            or vector.favorite_contact
            or any(k in lower_txt for k in ["call", "match tonight", "reached home", "had dinner", "don't call now", "talk tomorrow"])
        )

        if is_personal_chat:
            is_direct_request = (
                vector.favorite_contact
                or vector.contains_question
                or "@u_" in lower_txt
                or any(k in lower_txt for k in ["can you call", "call me", "pls call", "when you get 5 mins"])
            ) and not any(k in lower_txt for k in ["don't call now", "nothing urgent", "no need to reply", "no pressure"])

            action = "notify" if is_direct_request else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="personal",
                reason=f"Direct personal message from contact routed to {action}.",
                confidence=0.88,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
