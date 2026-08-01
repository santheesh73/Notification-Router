"""In-Memory Retrieval Cache."""

from src.retrieval.retrieval_result import RetrievalResult
from src.utils.logger import logger


class RetrievalCache:
    """In-memory cache for storing and retrieving RetrievalResult instances by message_id."""

    def __init__(self) -> None:
        """Initialize RetrievalCache."""
        self._cache: dict[str, RetrievalResult] = {}
        self.hits: int = 0
        self.misses: int = 0

    def get(self, message_id: str) -> RetrievalResult | None:
        """Get cached RetrievalResult for a message_id.

        Args:
            message_id: Message identifier.

        Returns:
            RetrievalResult if found in cache, else None.
        """
        if message_id in self._cache:
            self.hits += 1
            logger.debug(f"RetrievalCache HIT for message '{message_id}'.")
            return self._cache[message_id]

        self.misses += 1
        return None

    def set(self, message_id: str, result: RetrievalResult) -> None:
        """Store RetrievalResult in cache.

        Args:
            message_id: Message identifier.
            result: RetrievalResult instance.
        """
        self._cache[message_id] = result

    def clear(self) -> None:
        """Clear cache entries and reset metrics."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.hits + self.misses
        return round(self.hits / total, 4) if total > 0 else 0.0
