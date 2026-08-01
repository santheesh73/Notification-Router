"""MediaResult Data Model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaResult:
    """Dataclass holding extracted semantic understanding from image or audio media."""

    message_id: str
    media_type: str = "none"  # "image", "voice", "none"
    processed: bool = False
    summary: str = ""
    classification: str = "Unknown"
    entities: list[str] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)
    times: list[str] = field(default_factory=list)
    amounts: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    urgency: str = "low"  # "low", "medium", "high", "critical"
    risk: str = "low"  # "low", "medium", "high"
    confidence: float = 0.0
    raw_output: dict[str, Any] = field(default_factory=dict)
