"""Confidence Calibration Engine."""

from src.confidence.calibration import ConfidenceCalibrator
from src.confidence.scoring import ScoringEngine
from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult


class ConfidenceEngine:
    """Computes and calibrates unified confidence scores across multi-phase signals."""

    def __init__(
        self,
        scoring_engine: ScoringEngine | None = None,
        calibrator: ConfidenceCalibrator | None = None,
    ) -> None:
        """Initialize ConfidenceEngine.

        Args:
            scoring_engine: ScoringEngine instance.
            calibrator: ConfidenceCalibrator instance.
        """
        self.scoring_engine: ScoringEngine = scoring_engine or ScoringEngine()
        self.calibrator: ConfidenceCalibrator = calibrator or ConfidenceCalibrator()

    def compute_confidence(
        self,
        rule_result: RuleResult,
        llm_result: DecisionResult,
        retrieval_result: RetrievalResult | None,
        media_result: MediaResult | None,
        vector: FeatureVector,
        action: str,
    ) -> float:
        """Compute calibrated confidence score.

        Args:
            rule_result: RuleResult instance.
            llm_result: DecisionResult instance.
            retrieval_result: RetrievalResult instance or None.
            media_result: MediaResult instance or None.
            vector: FeatureVector instance.
            action: Resolved routing action string.

        Returns:
            Calibrated confidence float bounded in [0.0, 1.0].
        """
        base = self.scoring_engine.compute_base_score(rule_result, llm_result, retrieval_result, media_result)
        return self.calibrator.calibrate(base, vector, retrieval_result, action)
