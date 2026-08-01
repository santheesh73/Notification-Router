"""Threshold Tuner for Confidence Calibration Bounds."""

from src.utils.logger import logger


class ThresholdTuner:
    """Tunes feature and rule confidence thresholds dynamically."""

    def tune_thresholds(self, default_threshold: float = 0.70) -> dict[str, float]:
        """Generate tuned confidence thresholds for rule categories.

        Args:
            default_threshold: Base confidence threshold.

        Returns:
            Dictionary of category to tuned float threshold.
        """
        tuned = {
            "scam_threshold": 0.95,
            "urgent_threshold": 0.88,
            "payment_threshold": 0.90,
            "spam_threshold": 0.92,
            "muted_group_threshold": 0.99,
            "promotion_threshold": 0.75,
            "greeting_threshold": 0.70,
            "general_threshold": default_threshold,
        }
        logger.info("Threshold Tuner: Configured category-specific confidence bounds.")
        return tuned
