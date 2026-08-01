"""Unit tests for RetrievalCache."""

from src.retrieval.cache import RetrievalCache
from src.retrieval.retrieval_result import RetrievalResult


def test_retrieval_cache() -> None:
    """Test cache operations and hit/miss metrics."""
    cache = RetrievalCache()

    res = RetrievalResult(message_id="MSG_CACHE", retrieved=True, evidence_message_ids=["MH_001"])
    cache.set("MSG_CACHE", res)

    fetched = cache.get("MSG_CACHE")
    assert fetched is not None
    assert fetched.message_id == "MSG_CACHE"
    assert cache.hits == 1

    miss = cache.get("NON_EXISTENT")
    assert miss is None
    assert cache.misses == 1

    assert cache.hit_rate == 0.5
