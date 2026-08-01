"""Performance Benchmark Engine."""

from dataclasses import asdict, dataclass
import os
import time
import tracemalloc
from typing import Any

from src.confidence.final_decision import FinalDecision
from src.utils.logger import logger


@dataclass
class BenchmarkReport:
    """Dataclass holding benchmark measurement metrics."""

    total_messages: int = 0
    total_execution_time_seconds: float = 0.0
    messages_per_second: float = 0.0
    average_latency_ms: float = 0.0
    peak_memory_mb: float = 0.0
    average_confidence: float = 0.0
    rule_resolution_rate: float = 0.0
    llm_resolution_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class PerformanceBenchmark:
    """Measures runtime memory, CPU throughput, latency, and resolution rates."""

    def __init__(self) -> None:
        """Initialize PerformanceBenchmark."""
        self._start_time: float = 0.0

    def start(self) -> None:
        """Start benchmark measurement and tracemalloc memory profiling."""
        tracemalloc.start()
        self._start_time = time.perf_counter()
        logger.info("Started performance benchmark profiling...")

    def stop(self, decisions: list[FinalDecision]) -> BenchmarkReport:
        """Stop benchmark measurement and return compiled BenchmarkReport.

        Args:
            decisions: List of FinalDecision instances.

        Returns:
            BenchmarkReport instance.
        """
        elapsed = max(0.0001, time.perf_counter() - self._start_time)
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mem_mb = round(peak_mem / (1024 * 1024), 4)
        total_msgs = len(decisions)
        mps = round(total_msgs / elapsed, 2)
        avg_lat_ms = round((elapsed / total_msgs) * 1000.0, 2) if total_msgs > 0 else 0.0

        rule_cnt = sum(1 for d in decisions if d.decision_source == "RULE_ENGINE")
        llm_cnt = sum(1 for d in decisions if d.decision_source == "LLM" or d.resolved_by_ai)

        rule_rate = round((rule_cnt / total_msgs) * 100.0, 2) if total_msgs > 0 else 0.0
        llm_rate = round((llm_cnt / total_msgs) * 100.0, 2) if total_msgs > 0 else 0.0
        avg_conf = (
            round(sum(d.confidence for d in decisions) / total_msgs, 4)
            if total_msgs > 0
            else 0.0
        )

        report = BenchmarkReport(
            total_messages=total_msgs,
            total_execution_time_seconds=round(elapsed, 4),
            messages_per_second=mps,
            average_latency_ms=avg_lat_ms,
            peak_memory_mb=peak_mem_mb,
            average_confidence=avg_conf,
            rule_resolution_rate=rule_rate,
            llm_resolution_rate=llm_rate,
        )

        logger.info(f"Performance Benchmark complete: {mps} msg/s, Peak Mem: {peak_mem_mb} MB")
        return report
