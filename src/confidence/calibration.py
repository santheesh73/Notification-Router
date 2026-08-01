"""Confidence Score Calibrator."""

from src.features.feature_vector import FeatureVector
from src.retrieval.retrieval_result import RetrievalResult


class ConfidenceCalibrator:
    """Calibrates confidence scores based on contextual signals, evidence, trust, and risk factors."""

    def calibrate(
        self,
        base_score: float,
        vector: FeatureVector,
        retrieval_result: RetrievalResult | None,
        action: str,
    ) -> float:
        """Calibrate base confidence score using explicit signal additions.

        Formula:
            Confidence = Rule/Base Score + Evidence Score + Business Trust + Sender Trust + History Match + Media Confidence

        Args:
            base_score: Raw base score float.
            vector: Extracted FeatureVector instance.
            retrieval_result: RetrievalResult instance or None.
            action: Resolved decision action string.

        Returns:
            Calibrated confidence float bounded in [0.50, 0.99].
        """
        score = base_score

        # 1. Evidence Score (+0.02 per evidence ID up to +0.06)
        if retrieval_result and retrieval_result.evidence_message_ids:
            score += min(0.06, len(retrieval_result.evidence_message_ids) * 0.02)

        # 2. Business Trust (+0.04)
        if vector.trusted_business or vector.verified:
            score += 0.04

        # 3. Sender Trust (+0.04)
        if vector.trusted_sender or vector.favorite_contact:
            score += 0.04

        # 4. History Match (+0.03)
        if vector.interaction_frequency > 0.2 or vector.reply_history > 0:
            score += 0.03

        # Clamp strictly between 0.50 and 0.99
        return round(min(0.99, max(0.50, score)), 4)
