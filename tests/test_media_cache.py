"""Unit tests for MediaCache."""

from src.media.media_cache import MediaCache
from src.media.media_result import MediaResult


def test_media_cache() -> None:
    """Test MediaCache storing, retrieving, and hit rate."""
    cache = MediaCache()

    res = MediaResult(message_id="MSG_M1", media_type="image", processed=True, classification="Invoice")
    cache.set("IMG_001", res)

    fetched = cache.get("IMG_001")
    assert fetched is not None
    assert fetched.message_id == "MSG_M1"
    assert cache.hits == 1

    miss = cache.get("IMG_999")
    assert miss is None
    assert cache.misses == 1

    assert cache.hit_rate == 0.5
