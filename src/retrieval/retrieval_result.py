"""RetrievalResult Data Model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalResult:
    """Dataclass holding historical evidence retrieval outputs."""

    message_id: str
    retrieved: bool
    evidence_message_ids: list[str] = field(default_factory=list)
    retrieval_score: float = 0.0
    matched_strategy: str = "none"
    matched_keywords: list[str] = field(default_factory=list)
    similarity_details: dict[str, Any] = field(default_factory=dict)
