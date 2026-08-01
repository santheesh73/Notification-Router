"""LLM Router coordinating Hybrid Multi-LLM Routing across message batches."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.llm.hybrid_router import HybridLLMRouter
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


@dataclass
class DecisionValidationReport:
    """Dataclass holding validation report for AI Decision Orchestrator outputs."""

    missing_message_ids: list[str] = field(default_factory=list)
    invalid_confidences: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors are found."""
        return len(self.missing_message_ids) == 0 and len(self.invalid_confidences) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class LLMRouter:
    """Batch router coordinating Hybrid Multi-LLM Router execution across message batches."""

    def __init__(self, orchestrator: Any = None, hybrid_router: HybridLLMRouter | None = None) -> None:
        """Initialize LLMRouter.

        Args:
            orchestrator: Optional legacy orchestrator instance.
            hybrid_router: Optional HybridLLMRouter instance.
        """
        self.hybrid_router: HybridLLMRouter = hybrid_router or HybridLLMRouter()

    def process_batch(
        self,
        vectors: list[FeatureVector],
        rule_results: list[RuleResult],
        context: ContextManager,
        media_results: list[MediaResult] | None = None,
        retrieval_results: list[RetrievalResult] | None = None,
    ) -> list[DecisionResult]:
        """Process a batch of FeatureVectors and route unresolved messages to Hybrid Multi-LLM Router.

        Args:
            vectors: List of FeatureVectors.
            rule_results: List of Phase 4 RuleResults.
            context: ContextManager instance.
            media_results: Optional list of Phase 6 MediaResults.
            retrieval_results: Optional list of Phase 5 RetrievalResults.

        Returns:
            List of DecisionResult instances.
        """
        return self.hybrid_router.process_batch(
            vectors=vectors,
            rule_results=rule_results,
            context=context,
            media_results=media_results,
            retrieval_results=retrieval_results,
        )

    def _is_rule_resolved(
        self,
        vector: FeatureVector,
        rule_result: RuleResult,
        media_map: dict[str, Any] | None = None,
    ) -> bool:
        """Check if message is deterministically resolved by Rule Engine using category-specific thresholds."""
        return self.hybrid_router._is_rule_resolved(vector, rule_result, media_map)

    def validate(self, results: list[DecisionResult]) -> DecisionValidationReport:
        """Validate DecisionResult outputs.

        Args:
            results: List of DecisionResult instances.

        Returns:
            DecisionValidationReport object.
        """
        report = DecisionValidationReport()
        for res in results:
            if not res.message_id:
                report.missing_message_ids.append(res.message_id)
            if res.confidence < 0.0 or res.confidence > 1.0:
                report.invalid_confidences.append(f"{res.message_id}: {res.confidence}")
        return report

    def summary(self, results: list[DecisionResult]) -> str:
        """Generate statistical summary report across AI outputs."""
        return self.hybrid_router.generate_report()
