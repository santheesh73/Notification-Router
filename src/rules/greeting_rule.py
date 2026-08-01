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
        super().__init__(name="GreetingRule", priority=RulePriority.LOW)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_greeting = vector.contains_greeting or vector.contains_thank_you
        text_content = getattr(vector, "message_text", "") or ""
        if not is_greeting and text_content:
            lower_txt = str(text_content).lower()
            if any(kw in lower_txt for kw in GREETING_KEYWORDS):
                is_greeting = True

        if is_greeting:
            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="digest",
                message_type="greeting",
                reason="Casual greeting or pleasantry routed to digest.",
                confidence=0.90,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
