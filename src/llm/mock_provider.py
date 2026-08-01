"""Mock LLM Provider for deterministic testing."""

import json

from src.llm.llm_provider import LLMProvider


class MockProvider(LLMProvider):
    """Mock LLM Provider returning deterministic valid JSON responses."""

    def __init__(self) -> None:
        super().__init__(name="Mock")

    def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "payment" in prompt_lower or "invoice" in prompt_lower or "bank" in prompt_lower:
            return json.dumps({
                "action": "notify",
                "message_type": "payment",
                "reason": "Trusted business reminder for an active payment.",
                "confidence": 0.87,
            })
        elif "urgent" in prompt_lower or "hospital" in prompt_lower:
            return json.dumps({
                "action": "notify",
                "message_type": "urgent",
                "reason": "Time-sensitive emergency notice requiring immediate attention.",
                "confidence": 0.95,
            })
        elif "discount" in prompt_lower or "coupon" in prompt_lower:
            return json.dumps({
                "action": "digest",
                "message_type": "promotion",
                "reason": "Marketing offer compiled into daily summary.",
                "confidence": 0.78,
            })
        else:
            return json.dumps({
                "action": "digest",
                "message_type": "personal",
                "reason": "General contextual direct message routed to digest.",
                "confidence": 0.82,
            })

    def health_check(self) -> bool:
        return True

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))
