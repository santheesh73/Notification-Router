"""Retrieval Pipeline and Batch Executor."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.retrieval.retrieval_engine import RetrievalEngine
from src.retrieval.retrieval_result import RetrievalResult
from src.utils.logger import logger


@dataclass
class RetrievalValidationReport:
    """Dataclass holding validation report for retrieval outputs."""

    duplicate_evidence_ids: list[str] = field(default_factory=list)
    missing_message_ids: list[str] = field(default_factory=list)
    invalid_retrieval_scores: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors are found."""
        return (
            len(self.duplicate_evidence_ids) == 0
            and len(self.missing_message_ids) == 0
            and len(self.invalid_retrieval_scores) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class RetrievalPipeline:
    """Batch orchestrator for evidence retrieval across dataset feature vectors."""

    def __init__(self, engine: RetrievalEngine | None = None) -> None:
        """Initialize RetrievalPipeline.

        Args:
            engine: RetrievalEngine instance.
        """
        self.engine: RetrievalEngine = engine or RetrievalEngine()

    def process_batch(
        self,
        vectors: list[FeatureVector],
        context: ContextManager,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """Process a batch of FeatureVectors and retrieve Top-K evidence for each.

        Args:
            vectors: List of FeatureVectors.
            context: ContextManager instance.
            top_k: Number of evidence items per message.

        Returns:
            List of RetrievalResult instances.
        """
        logger.info(f"Retrieving evidence for {len(vectors)} FeatureVectors...")
        results: list[RetrievalResult] = []
        for vec in vectors:
            res = self.engine.retrieve(vec, context, top_k=top_k)
            results.append(res)
        logger.success(f"Successfully processed retrieval for {len(results)} messages.")
        return results

    def validate(self, results: list[RetrievalResult]) -> RetrievalValidationReport:
        """Validate RetrievalResult instances.

        Args:
            results: List of RetrievalResult instances.

        Returns:
            RetrievalValidationReport object.
        """
        report = RetrievalValidationReport()

        for res in results:
            if not res.message_id:
                report.missing_message_ids.append(res.message_id)

            if len(res.evidence_message_ids) != len(set(res.evidence_message_ids)):
                report.duplicate_evidence_ids.append(res.message_id)

            if res.retrieval_score < 0.0 or res.retrieval_score > 1.0:
                report.invalid_retrieval_scores.append(f"{res.message_id}: {res.retrieval_score}")

        logger.info(f"Retrieval validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self, results: list[RetrievalResult]) -> str:
        """Generate statistical summary report across retrieval results.

        Args:
            results: List of RetrievalResult instances.

        Returns:
            Formatted ASCII summary table string.
        """
        if not results:
            return "No RetrievalResults available for summary."

        total_r = len(results)
        retrieved_cnt = sum(1 for r in results if r.retrieved and len(r.evidence_message_ids) > 0)
        no_evidence_cnt = total_r - retrieved_cnt

        avg_evidence_count = sum(len(r.evidence_message_ids) for r in results) / total_r
        avg_score = sum(r.retrieval_score for r in results) / total_r

        # Strategy usage
        strategy_counts: dict[str, int] = {}
        for r in results:
            s_name = r.matched_strategy
            strategy_counts[s_name] = strategy_counts.get(s_name, 0) + 1

        rows = [
            ["Total Messages Evaluated", total_r],
            ["Messages With Evidence", f"{retrieved_cnt} ({(retrieved_cnt / total_r) * 100:.1f}%)"],
            ["Messages Without Evidence", f"{no_evidence_cnt} ({(no_evidence_cnt / total_r) * 100:.1f}%)"],
            ["Average Evidence Items Per Message", f"{avg_evidence_count:.2f}"],
            ["Average Retrieval Score", f"{avg_score:.4f}"],
            ["Cache Hit Rate", f"{self.engine.cache.hit_rate * 100:.1f}%"],
            ["Top Matched Strategies", ", ".join([f"{k}:{v}" for k, v in strategy_counts.items()])],
        ]

        return tabulate(rows, headers=["Retrieval Metric", "Value"], tablefmt="grid")
