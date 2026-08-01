"""Abstract Base Retrieval Strategy."""

from abc import ABC, abstractmethod

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile


class BaseRetrievalStrategy(ABC):
    """Abstract base class for all deterministic historical evidence retrieval strategies."""

    def __init__(self, name: str) -> None:
        """Initialize BaseRetrievalStrategy.

        Args:
            name: Strategy identifier name.
        """
        self.name: str = name

    @abstractmethod
    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        """Score candidate historical messages based on strategy criteria.

        Args:
            vector: Extracted FeatureVector of the current message.
            candidates: List of historical HistoryProfile records.
            context: ContextManager instance.

        Returns:
            Dictionary mapping candidate message_id to score float (0.0 to 1.0).
        """
        pass
