"""Pipeline Progress Tracker."""

import time

from src.utils.logger import logger


class ProgressTracker:
    """Tracks execution progress, resolution metrics, and estimates throughput/ETA."""

    def __init__(self, total_messages: int) -> None:
        """Initialize ProgressTracker.

        Args:
            total_messages: Total number of messages to process.
        """
        self.total_messages: int = max(1, total_messages)
        self.processed_count: int = 0
        self.rule_resolved_count: int = 0
        self.ai_resolved_count: int = 0
        self.failed_count: int = 0
        self.start_time: float = time.perf_counter()

    def update(
        self,
        message_id: str,
        resolved_by_rule: bool,
        resolved_by_ai: bool,
        failed: bool = False,
    ) -> None:
        """Update tracker state with result for a processed message.

        Args:
            message_id: Message identifier string.
            resolved_by_rule: Set to True if resolved by Rule Engine.
            resolved_by_ai: Set to True if resolved by LLM Orchestrator.
            failed: Set to True if processing encountered error and fallback was used.
        """
        self.processed_count += 1
        if failed:
            self.failed_count += 1
        elif resolved_by_rule:
            self.rule_resolved_count += 1
        elif resolved_by_ai:
            self.ai_resolved_count += 1

        pct = self.percentage
        mps = self.messages_per_sec
        eta = self.eta_seconds

        logger.debug(
            f"Progress: [{self.processed_count}/{self.total_messages}] ({pct:.1f}%) | "
            f"Rule={self.rule_resolved_count}, AI={self.ai_resolved_count}, Failed={self.failed_count} | "
            f"Speed={mps:.1f} msg/s, ETA={eta:.1f}s"
        )

    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        return round((self.processed_count / self.total_messages) * 100.0, 2)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return max(0.001, time.perf_counter() - self.start_time)

    @property
    def messages_per_sec(self) -> float:
        """Get processing throughput in messages per second."""
        return round(self.processed_count / self.elapsed_time, 2)

    @property
    def eta_seconds(self) -> float:
        """Get estimated remaining time in seconds."""
        remaining = self.total_messages - self.processed_count
        speed = self.messages_per_sec
        return round(remaining / speed, 2) if speed > 0 else 0.0
