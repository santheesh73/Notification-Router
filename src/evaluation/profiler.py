"""Pipeline Execution Profiler."""

import time
from typing import Any

from tabulate import tabulate

from src.utils.logger import logger


class PipelineProfiler:
    """Measures execution timing across individual pipeline modules."""

    def __init__(self) -> None:
        """Initialize PipelineProfiler."""
        self.stage_timings: dict[str, float] = {}

    def record_stage(self, stage_name: str, elapsed_seconds: float) -> None:
        """Record execution time for a pipeline stage.

        Args:
            stage_name: Name of the pipeline stage.
            elapsed_seconds: Duration in seconds.
        """
        self.stage_timings[stage_name] = round(elapsed_seconds, 6)
        logger.debug(f"Profiler: Stage '{stage_name}' completed in {elapsed_seconds:.6f}s")

    def summary_table(self) -> str:
        """Generate formatted ASCII table of stage timings.

        Returns:
            Formatted ASCII table string.
        """
        if not self.stage_timings:
            return "No profiling records available."

        total_time = sum(self.stage_timings.values())
        rows: list[list[Any]] = []

        for stage, duration in self.stage_timings.items():
            pct = (duration / total_time * 100.0) if total_time > 0 else 0.0
            rows.append([stage, f"{duration:.6f}s", f"{pct:.1f}%"])

        rows.append(["Total End-to-End Pipeline", f"{total_time:.6f}s", "100.0%"])

        return tabulate(rows, headers=["Pipeline Stage", "Duration (Seconds)", "Percentage"], tablefmt="grid")
