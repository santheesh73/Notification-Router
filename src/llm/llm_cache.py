"""In-Memory LLM Response Cache."""

import hashlib

from src.llm.decision_result import DecisionResult
from src.utils.logger import logger


class LLMCache:
    """In-memory cache storing LLM decision outputs indexed by prompt MD5 hash."""

    def __init__(self) -> None:
        """Initialize LLMCache."""
        self._cache: dict[str, DecisionResult] = {}
        self.hits: int = 0
        self.misses: int = 0

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Compute MD5 hash hex string for input prompt.

        Args:
            prompt: Text prompt.

        Returns:
            MD5 hash hex string.
        """
        return hashlib.md5(prompt.encode("utf-8")).hexdigest()

    def get(self, prompt: str) -> DecisionResult | None:
        """Get cached DecisionResult for a prompt.

        Args:
            prompt: Text prompt string.

        Returns:
            DecisionResult if found in cache, else None.
        """
        prompt_hash = self.hash_prompt(prompt)
        if prompt_hash in self._cache:
            self.hits += 1
            logger.debug(f"LLMCache HIT for prompt hash '{prompt_hash[:8]}'.")
            res = self._cache[prompt_hash]
            # Return copy with cached=True
            return DecisionResult(
                message_id=res.message_id,
                action=res.action,
                message_type=res.message_type,
                reason=res.reason,
                confidence=res.confidence,
                provider=res.provider,
                latency=0.0,
                tokens=res.tokens,
                cached=True,
            )

        self.misses += 1
        return None

    def set(self, prompt: str, result: DecisionResult) -> None:
        """Store DecisionResult in cache.

        Args:
            prompt: Text prompt string.
            result: DecisionResult instance.
        """
        prompt_hash = self.hash_prompt(prompt)
        self._cache[prompt_hash] = result

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
