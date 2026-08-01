"""Adaptive Confidence Optimizer."""

from src.features.feature_vector import FeatureVector
from src.utils.logger import logger


class AdaptiveConfidenceOptimizer:
    """Optimizes adaptive confidence calibration dynamically based on signal interaction."""

    def optimize_confidence(
        self,
        base_confidence: float,
        vector: FeatureVector,
        evidence_count: int,
    ) -> float:
        """Dynamically calibrate base confidence.

        Args:
            base_confidence: Uncalibrated confidence float.
            vector: FeatureVector instance.
            evidence_count: Number of valid evidence items.

        Returns:
            Calibrated confidence float bounded in [0.0, 1.0].
        """
        score = base_confidence

        # Evidence count scaling
        if evidence_count >= 3:
            score += 0.04
        elif evidence_count == 0:
            score -= 0.03

        # Business verification bonus
        if vector.verified or vector.trusted_business:
            score += 0.03

        # Risk penalty for new unknown senders
        if vector.new_sender and vector.risk_score > 0.4:
            score -= 0.05

        calibrated = round(min(1.0, max(0.0, score)), 4)
        logger.debug(f"Adaptive Confidence Optimizer: Adjusted {base_confidence:.4f} -> {calibrated:.4f}")
        return calibrated
