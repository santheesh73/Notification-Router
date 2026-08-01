"""UserProfile Data Model."""

from dataclasses import dataclass, field


@dataclass
class UserProfile:
    """Dataclass representing structured user profile context."""

    user_id: str
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    opens: int = 0
    replies: int = 0
    dismissals: int = 0
    reports: int = 0
    notification_load: float = 0.0
    trusted_contacts: list[str] = field(default_factory=list)
    trusted_businesses: list[str] = field(default_factory=list)
    muted_groups: list[str] = field(default_factory=list)
    reply_rate: float = 0.0
    open_rate: float = 0.0
    dismiss_rate: float = 0.0
    report_rate: float = 0.0
    engagement_score: float = 0.0
    last_active: str | None = None
    favorite_groups: list[str] = field(default_factory=list)
    favorite_businesses: list[str] = field(default_factory=list)
