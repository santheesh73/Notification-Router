"""Unit tests for OutputEvaluator, PerformanceBenchmark, and MetricsCalculator."""

from pathlib import Path

from src.confidence.final_decision import FinalDecision
from src.evaluation.benchmark import BenchmarkReport, PerformanceBenchmark
from src.evaluation.metrics import MetricsCalculator, MetricsSummary
from src.evaluation.evaluator import OutputEvaluator


def test_metrics_calculator() -> None:
    """Test MetricsCalculator calculating distribution statistics."""
    decisions = [
        FinalDecision("M1", "notify", "payment", "Reason 1", 0.90, ["E1"], decision_source="RULE_ENGINE"),
        FinalDecision("M2", "digest", "event", "Reason 2", 0.80, ["E2"], decision_source="LLM", resolved_by_ai=True),
    ]

    calc = MetricsCalculator()
    summary = calc.compute_metrics(decisions)

    assert isinstance(summary, MetricsSummary)
    assert summary.total_messages == 2
    assert summary.action_counts["notify"] == 1
    assert summary.action_counts["digest"] == 1
    assert summary.average_confidence == 0.85


def test_performance_benchmark() -> None:
    """Test PerformanceBenchmark measuring execution throughput."""
    bench = PerformanceBenchmark()
    bench.start()

    decisions = [
        FinalDecision("M1", "notify", "payment", "Reason 1", 0.90, ["E1"], decision_source="RULE_ENGINE"),
    ]

    report = bench.stop(decisions)
    assert isinstance(report, BenchmarkReport)
    assert report.total_messages == 1
    assert report.messages_per_second > 0
    assert report.peak_memory_mb >= 0.0
