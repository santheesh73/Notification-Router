"""In-Memory Media Processing Cache."""

from src.media.media_result import MediaResult
from src.utils.logger import logger


class MediaCache:
    """In-memory cache for storing and retrieving MediaResult instances by media_id or message_id."""

    def __init__(self) -> None:
        """Initialize MediaCache."""
        self._cache: dict[str, MediaResult] = {}
        self.hits: int = 0
        self.misses: int = 0

    def get(self, key: str) -> MediaResult | None:
        """Get cached MediaResult by media_id or message_id.

        Args:
            key: Media or message identifier string.

        Returns:
            MediaResult if found in cache, else None.
        """
        if key in self._cache:
            self.hits += 1
            logger.debug(f"MediaCache HIT for key '{key}'.")
            return self._cache[key]

        self.misses += 1
        return None

    def set(self, key: str, result: MediaResult) -> None:
        """Store MediaResult in cache.

        Args:
            key: Media or message identifier string.
            result: MediaResult instance.
        """
        self._cache[key] = result

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
