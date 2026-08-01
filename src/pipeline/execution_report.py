"""Execution Report Generator."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from config.settings import LOGS_PATH
from src.confidence.final_decision import FinalDecision
from src.pipeline.progress_tracker import ProgressTracker
from src.utils.logger import logger


class ExecutionReportGenerator:
    """Generates execution_report.json documenting end-to-end pipeline run metrics."""

    def __init__(self, report_path: Path | None = None) -> None:
        """Initialize ExecutionReportGenerator.

        Args:
            report_path: Path to report JSON file. Defaults to logs/execution_report.json.
        """
        self.report_path: Path = report_path or (LOGS_PATH / "execution_report.json")
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure parent directory exists."""
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        decisions: list[FinalDecision],
        tracker: ProgressTracker,
    ) -> dict[str, Any]:
        """Generate and save execution report JSON.

        Args:
            decisions: List of FinalDecision instances.
            tracker: ProgressTracker instance.

        Returns:
            Generated report dictionary.
        """
        avg_conf = (
            sum(d.confidence for d in decisions) / len(decisions)
            if decisions
            else 0.0
        )

        report = {
            "total_processed": len(decisions),
            "messages_failed": tracker.failed_count,
            "rule_decisions": tracker.rule_resolved_count,
            "ai_decisions": tracker.ai_resolved_count,
            "average_confidence": round(avg_conf, 4),
            "total_processing_time_seconds": round(tracker.elapsed_time, 4),
            "messages_per_second": tracker.messages_per_sec,
            "finish_timestamp": datetime.now().isoformat(),
        }

        try:
            with open(self.report_path, mode="w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Generated execution report at: {self.report_path}")
        except Exception as exc:
            logger.error(f"Failed to write execution report: {exc}")

        return report
