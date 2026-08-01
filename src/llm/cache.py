"""SHA256 Prompt Cache for Multi-LLM Routing System."""

import hashlib
import time
from typing import Any

from src.utils.logger import logger


class PromptCache:
    """High-performance SHA256 prompt response cache to eliminate redundant LLM API calls."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 86400.0) -> None:
        """Initialize PromptCache.

        Args:
            max_size: Maximum entries in cache before eviction.
            ttl_seconds: Time-to-live per cache entry in seconds.
        """
        self.max_size: int = max_size
        self.ttl_seconds: float = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}
        self.hits: int = 0
        self.misses: int = 0

    @staticmethod
    def _compute_hash(prompt: str) -> str:
        """Compute SHA-256 digest string for a prompt string.

        Args:
            prompt: Text prompt string.

        Returns:
            Hexadecimal SHA256 string.
        """
        return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

    def get(self, prompt: str) -> dict[str, Any] | None:
        """Retrieve cached response dict by prompt string.

        Args:
            prompt: Prompt text.

        Returns:
            Cached response dictionary if found and unexpired, else None.
        """
        key = self._compute_hash(prompt)
        entry = self._cache.get(key)

        if not entry:
            self.misses += 1
            return None

        # Check TTL
        if time.time() - entry["timestamp"] > self.ttl_seconds:
            del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(f"PromptCache HIT for prompt hash key '{key[:8]}...'")
        response = dict(entry["response"])
        response["cached"] = True
        return response

    def put(self, prompt: str, response: dict[str, Any]) -> None:
        """Store prompt response in cache keyed by SHA256(prompt).

        Args:
            prompt: Prompt text string.
            response: Response dictionary to store.
        """
        if len(self._cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]

        key = self._compute_hash(prompt)
        self._cache[key] = {
            "response": dict(response),
            "timestamp": time.time(),
        }
        logger.debug(f"PromptCache STORED hash key '{key[:8]}...'")

    @property
    def hit_rate(self) -> float:
        """Compute hit rate fraction float."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
