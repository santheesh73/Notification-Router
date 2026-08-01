"""Rule Optimizer for Rule Engine Efficiency."""

from dataclasses import asdict, dataclass, field
from typing import Any

from src.rules.rule_result import RuleResult
from src.utils.logger import logger


@dataclass
class RuleOptimizationReport:
    """Dataclass holding rule analysis and optimization recommendations."""

    total_rules_evaluated: int = 0
    active_rules: list[str] = field(default_factory=list)
    rule_trigger_counts: dict[str, int] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class RuleOptimizer:
    """Analyzes Rule Engine results and recommends priority and threshold tuning."""

    def analyze_rule_performance(self, rule_results: list[RuleResult]) -> RuleOptimizationReport:
        """Analyze rule resolution distribution and generate optimization recommendations.

        Args:
            rule_results: List of RuleResult instances from Phase 4.

        Returns:
            RuleOptimizationReport object.
        """
        trigger_counts: dict[str, int] = {}
        for r in rule_results:
            if r.resolved:
                rule_name = r.triggered_rule
                trigger_counts[rule_name] = trigger_counts.get(rule_name, 0) + 1

        active_rules = list(trigger_counts.keys())
        recs: list[str] = []

        if "ScamRule" in active_rules:
            recs.append("Keep ScamRule at Priority.CRITICAL (Priority 1) to guarantee zero false negatives.")
        if "PaymentRule" in active_rules:
            recs.append("Maintain PaymentRule Priority.HIGH (Priority 2) for verified business transactions.")

        recs.append("Maintain 15-rule registry ordering: CRITICAL -> HIGH -> MEDIUM -> LOW.")

        report = RuleOptimizationReport(
            total_rules_evaluated=15,
            active_rules=active_rules,
            rule_trigger_counts=trigger_counts,
            recommendations=recs,
        )

        logger.info(f"Rule Optimization Analysis complete across {len(rule_results)} routing results.")
        return report
