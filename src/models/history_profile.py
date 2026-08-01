"""HistoryProfile Data Model."""

from dataclasses import dataclass


@dataclass
class HistoryProfile:
    """Dataclass representing structured message history interaction record."""

    message_id: str
    user_id: str
    sender: str
    conversation: str = "direct"
    group_id: str | None = None
    business_id: str | None = None
    message_text: str = ""
    media_type: str | None = None
    opened: bool = False
    replied: bool = False
    dismissed: bool = False
    reported: bool = False
    event_time: str | None = None
