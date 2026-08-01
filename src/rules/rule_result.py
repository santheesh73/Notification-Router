"""RuleResult Data Model."""

from dataclasses import dataclass


@dataclass
class RuleResult:
    """Dataclass holding deterministic routing decision output."""

    message_id: str
    resolved: bool
    action: str  # "notify", "digest", "mute", "unresolved"
    message_type: str  # "scam", "urgent", "spam", "payment", etc.
    reason: str
    confidence: float
    triggered_rule: str
    priority: str
    requires_ai: bool = False
