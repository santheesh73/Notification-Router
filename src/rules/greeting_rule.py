"""Greeting & Pleasantries Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult

GREETING_KEYWORDS = {
    "good morning",
    "good night",
    "happy birthday",
    "happy diwali",
    "happy new year",
    "festival",
    "hello",
    "hi ",
    "hey",
    "greetings",
}


class GreetingRule(BaseRule):
    """Routes casual greetings, wishes, and pleasantries (Priority: LOW)."""

    def __init__(self) -> None:
        super().__init__(name="GreetingRule", priority=RulePriority.HIGH)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        text_content = str(getattr(vector, "message_text", "") or "")
        lower_txt = text_content.lower()

        # Do not classify as greeting if stronger intent exists
        if vector.contains_question or getattr(vector, "event_score", 0) > 0 or getattr(vector, "promotion_score", 0) > 0 or any(k in lower_txt for k in ["call", "feedback", "pvr", "volunteer", "dinner", "match"]):
            return None

        gr_score = getattr(vector, "greeting_score", 0)
        is_greeting = gr_score > 0 or vector.contains_greeting or vector.contains_thank_you
        if not is_greeting and text_content:
            if any(kw in lower_txt for kw in GREETING_KEYWORDS):
                is_greeting = True

        if is_greeting:
            lower_txt = text_content.lower()
            is_forward_greeting = vector.is_forwarded or getattr(vector, "forward_probability", 0) > 0.5 or any(k in lower_txt for k in ["forwarding because", "forwarded", "share blessings", "share with everyone"])
            action = "mute" if is_forward_greeting else "digest"
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action=action,
                message_type="greeting",
                reason=f"Casual greeting or pleasantry routed to {action}.",
                confidence=0.88,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
