"""GroupProfile Data Model."""

from dataclasses import dataclass, field


@dataclass
class GroupProfile:
    """Dataclass representing structured WhatsApp group profile context."""

    group_id: str
    group_name: str
    group_type: str = "Other"
    member_count: int = 0
    admin_count: int = 0
    recent_activity: int = 0
    activity_score: float = 0.0
    user_participation: dict[str, int] = field(default_factory=dict)
    mute_state: dict[str, bool] = field(default_factory=dict)
    importance_score: float = 0.0
