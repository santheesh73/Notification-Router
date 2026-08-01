"""Raw Confidence Scoring Engine."""

from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult


class ScoringEngine:
    """Computes base weighted confidence score across multi-phase signals."""

    def compute_base_score(
        self,
        rule_result: RuleResult,
        llm_result: DecisionResult,
        retrieval_result: RetrievalResult | None,
        media_result: MediaResult | None,
    ) -> float:
        """Calculate weighted base confidence score.

        Args:
            rule_result: RuleResult instance.
            llm_result: DecisionResult instance.
            retrieval_result: RetrievalResult instance or None.
            media_result: MediaResult instance or None.

        Returns:
            Weighted base score float.
        """
        if rule_result.resolved:
            base = rule_result.confidence
        elif llm_result and llm_result.provider != "RuleEngine":
            base = llm_result.confidence
        else:
            base = 0.58

        return round(min(0.99, max(0.50, base)), 4)
