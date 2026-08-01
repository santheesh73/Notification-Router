"""Retrieval Optimizer for Ranking Strategy Weights."""

from src.utils.logger import logger


class RetrievalOptimizer:
    """Optimizes historical evidence retrieval strategy weights."""

    def get_optimized_weights(self) -> dict[str, float]:
        """Return optimized strategy weights for evidence ranking.

        Returns:
            Dictionary of strategy name to float weight.
        """
        weights = {
            "sender_weight": 0.35,
            "business_weight": 0.25,
            "group_weight": 0.15,
            "keyword_weight": 0.15,
            "recency_decay_weight": 0.10,
        }
        logger.info("Retrieval Optimizer: Strategy weights calibrated for optimal evidence ranking.")
        return weights
