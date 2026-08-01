"""DecisionResult Data Model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionResult:
    """Dataclass holding AI Decision Orchestrator routing output."""

    message_id: str
    action: str = "digest"  # "notify", "digest", "mute"
    message_type: str = "unknown"  # "personal", "urgent", "event", "payment", "business_update", "promotion", "greeting", "forward", "spam", "scam", "unknown"
    reason: str = ""
    confidence: float = 0.50
    provider: str = "Mock"
    latency: float = 0.0
    tokens: dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    cached: bool = False
