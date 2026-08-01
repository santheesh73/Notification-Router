"""Rule Pipeline and Batch Router."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.rule_engine import NotificationRuleEngine
from src.rules.rule_result import RuleResult
from src.utils.logger import logger

VALID_ACTIONS: set[str] = {"notify", "digest", "mute", "unresolved"}
VALID_MESSAGE_TYPES: set[str] = {
    "scam",
    "spam",
    "urgent",
    "payment",
    "business",
    "business_update",
    "greeting",
    "event",
    "reminder",
    "personal",
    "family",
    "office",
    "muted_group",
    "forward",
    "duplicate",
    "promotion",
    "general",
}


@dataclass
class RuleValidationReport:
    """Dataclass holding validation report for rule routing outputs."""

    unknown_actions: list[str] = field(default_factory=list)
    unknown_message_types: list[str] = field(default_factory=list)
    missing_reasons: list[str] = field(default_factory=list)
    invalid_confidences: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors are found."""
        return (
            len(self.unknown_actions) == 0
            and len(self.unknown_message_types) == 0
            and len(self.missing_reasons) == 0
            and len(self.invalid_confidences) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class RulePipeline:
    """Batch orchestrator for routing FeatureVectors through NotificationRuleEngine."""

    def __init__(self, engine: NotificationRuleEngine | None = None) -> None:
        """Initialize RulePipeline.

        Args:
            engine: NotificationRuleEngine instance.
        """
        self.engine: NotificationRuleEngine = engine or NotificationRuleEngine()

    def route_batch(
        self,
        vectors: list[FeatureVector],
        context: ContextManager,
    ) -> list[RuleResult]:
        """Route a batch of FeatureVectors through the rule engine.

        Args:
            vectors: List of FeatureVector instances.
            context: ContextManager instance.

        Returns:
            List of RuleResult instances.
        """
        logger.info(f"Routing batch of {len(vectors)} FeatureVectors through Rule Engine...")
        results: list[RuleResult] = []
        for vec in vectors:
            res = self.engine.route(vec, context)
            results.append(res)
        logger.success(f"Rule Engine finished routing {len(results)} messages.")
        return results

    def validate(self, results: list[RuleResult]) -> RuleValidationReport:
        """Validate RuleResult outputs.

        Args:
            results: List of RuleResult instances.

        Returns:
            RuleValidationReport object.
        """
        report = RuleValidationReport()

        for res in results:
            if res.action not in VALID_ACTIONS:
                report.unknown_actions.append(f"{res.message_id}: {res.action}")

            if res.message_type not in VALID_MESSAGE_TYPES:
                report.unknown_message_types.append(f"{res.message_id}: {res.message_type}")

            if not res.reason or not res.reason.strip():
                report.missing_reasons.append(res.message_id)

            if res.confidence < 0.0 or res.confidence > 1.0:
                report.invalid_confidences.append(f"{res.message_id}: {res.confidence}")

        logger.info(f"Rule validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self, results: list[RuleResult]) -> str:
        """Generate statistical summary table across routing results.

        Args:
            results: List of RuleResult instances.

        Returns:
            Formatted ASCII summary table string.
        """
        if not results:
            return "No RuleResults available for summary."

        total_r = len(results)
        resolved_cnt = sum(1 for r in results if r.resolved)
        unresolved_cnt = sum(1 for r in results if not r.resolved)
        resolved_pct = (resolved_cnt / total_r) * 100.0 if total_r > 0 else 0.0

        notify_cnt = sum(1 for r in results if r.action == "notify")
        digest_cnt = sum(1 for r in results if r.action == "digest")
        mute_cnt = sum(1 for r in results if r.action == "mute")

        scam_cnt = sum(1 for r in results if r.message_type == "scam")
        spam_cnt = sum(1 for r in results if r.message_type == "spam")

        conf_sum = sum(r.confidence for r in results if r.resolved)
        avg_conf = conf_sum / resolved_cnt if resolved_cnt > 0 else 0.0

        rows = [
            ["Total Messages Routed", total_r],
            ["Messages Resolved", f"{resolved_cnt} ({resolved_pct:.1f}%)"],
            ["Messages Unresolved (Requires AI)", f"{unresolved_cnt} ({100.0 - resolved_pct:.1f}%)"],
            ["Action: Notify Count", notify_cnt],
            ["Action: Digest Count", digest_cnt],
            ["Action: Mute Count", mute_cnt],
            ["Scam Messages Detected", scam_cnt],
            ["Spam Messages Detected", spam_cnt],
            ["Average Rule Confidence", f"{avg_conf:.4f}"],
        ]

        return tabulate(rows, headers=["Rule Engine Metric", "Value"], tablefmt="grid")
