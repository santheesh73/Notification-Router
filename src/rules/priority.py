"""Rule Priority Constants and Enum."""

from enum import IntEnum


class RulePriority(IntEnum):
    """Execution priority levels for deterministic rules (lower integer = higher priority)."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    def __str__(self) -> str:
        return self.name
