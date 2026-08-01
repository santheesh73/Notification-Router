"""Metrics Calculator for Routing Evaluation."""

from dataclasses import asdict, dataclass, field
import statistics
from typing import Any

from src.confidence.final_decision import FinalDecision


@dataclass
class MetricsSummary:
    """Dataclass encapsulating aggregated evaluation metrics."""

    total_messages: int = 0
    action_counts: dict[str, int] = field(default_factory=dict)
    message_type_counts: dict[str, int] = field(default_factory=dict)
    decision_source_counts: dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0
    min_confidence: float = 0.0
    max_confidence: float = 0.0
    evidence_coverage_count: int = 0
    evidence_coverage_rate: float = 0.0
    rule_resolution_rate: float = 0.0
    llm_resolution_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics summary to dictionary."""
        return asdict(self)


class MetricsCalculator:
    """Computes statistical distribution metrics across FinalDecision results."""

    def compute_metrics(self, decisions: list[FinalDecision]) -> MetricsSummary:
        """Compute metrics from a list of FinalDecision instances.

        Args:
            decisions: List of FinalDecision instances.

        Returns:
            MetricsSummary dataclass instance.
        """
        if not decisions:
            return MetricsSummary()

        total = len(decisions)
        action_counts: dict[str, int] = {}
        type_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        confidences: list[float] = []
        ev_count = 0
        rule_cnt = 0
        llm_cnt = 0

        for dec in decisions:
            action_counts[dec.action] = action_counts.get(dec.action, 0) + 1
            type_counts[dec.message_type] = type_counts.get(dec.message_type, 0) + 1
            source_counts[dec.decision_source] = source_counts.get(dec.decision_source, 0) + 1
            confidences.append(float(dec.confidence))

            if dec.evidence_message_ids and len(dec.evidence_message_ids) > 0 and dec.evidence_message_ids[0] != "none":
                ev_count += 1

            if getattr(dec, "resolved_by_ai", False) or "LLM" in str(dec.decision_source):
                llm_cnt += 1
            elif dec.decision_source == "FALLBACK":
                pass
            else:
                rule_cnt += 1

        avg_conf = round(statistics.mean(confidences), 4) if confidences else 0.0
        min_conf = round(min(confidences), 4) if confidences else 0.0
        max_conf = round(max(confidences), 4) if confidences else 0.0
        ev_rate = round((ev_count / total) * 100.0, 1) if total > 0 else 0.0
        rule_rate = round((rule_cnt / total) * 100.0, 1) if total > 0 else 0.0
        llm_rate = round((llm_cnt / total) * 100.0, 1) if total > 0 else 0.0

        return MetricsSummary(
            total_messages=total,
            action_counts=action_counts,
            message_type_counts=type_counts,
            decision_source_counts=source_counts,
            average_confidence=avg_conf,
            min_confidence=min_conf,
            max_confidence=max_conf,
            evidence_coverage_count=ev_count,
            evidence_coverage_rate=ev_rate,
            rule_resolution_rate=rule_rate,
            llm_resolution_rate=llm_rate,
        )
