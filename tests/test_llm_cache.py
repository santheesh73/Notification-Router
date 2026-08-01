"""Unit tests for LLMCache."""

from src.llm.decision_result import DecisionResult
from src.llm.llm_cache import LLMCache


def test_llm_cache() -> None:
    """Test LLMCache set, get, and hit rate."""
    cache = LLMCache()

    res = DecisionResult(message_id="MSG_C1", action="notify", confidence=0.88)
    prompt = "Sample prompt for cache testing"

    cache.set(prompt, res)

    fetched = cache.get(prompt)
    assert fetched is not None
    assert fetched.message_id == "MSG_C1"
    assert fetched.cached is True
    assert cache.hits == 1

    miss = cache.get("Uncached prompt text")
    assert miss is None
    assert cache.misses == 1

    assert cache.hit_rate == 0.5
