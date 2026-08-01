"""FinalDecision Data Model."""

from dataclasses import dataclass, field


@dataclass
class FinalDecision:
    """Dataclass representing the final, calibrated notification routing decision for output generation."""

    message_id: str
    action: str = "digest"  # "notify", "digest", "mute"
    message_type: str = "unknown"  # "personal", "urgent", "event", "payment", "business_update", "promotion", "greeting", "forward", "spam", "scam", "unknown"
    reason: str = ""
    confidence: float = 0.50
    evidence_message_ids: list[str] = field(default_factory=list)
    decision_source: str = "FALLBACK"  # "RULE_ENGINE", "LLM", "FUSED", "FALLBACK"
    rule_used: str = "None"
    llm_provider: str = "None"
    resolved_by_ai: bool = False
    processing_time: float = 0.0
