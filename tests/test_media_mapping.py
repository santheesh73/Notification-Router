"""Unit tests for MediaManager repository mapping and caching."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.loaders.load_data import DataRepository
from src.media.media_manager import MediaManager


def test_media_mapping_loading() -> None:
    """Test loading repository mappings from images.csv and voice_notes.csv."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    mgr = MediaManager(repository=repo)
    img_map, voice_map = mgr.load_repository_mappings(repo)

    assert isinstance(img_map, dict)
    assert isinstance(voice_map, dict)
    assert len(img_map) > 0
    assert len(voice_map) > 0


def test_media_mapping_correctness() -> None:
    """Test mapping correctness for known media IDs."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    mgr = MediaManager(repository=repo)
    assert "img_001" in mgr.image_map
    assert "vn_001" in mgr.voice_map

    assert Path(mgr.image_map["img_001"]).suffix in [".jpg", ".png", ".jpeg", ".webp", ".bmp"]
    assert Path(mgr.voice_map["vn_001"]).suffix in [".mp3", ".wav", ".m4a", ".ogg", ".aac"]


def test_media_mapping_cache_reuse() -> None:
    """Test that repository mappings are cached and loaded only once."""
    mgr = MediaManager()
    assert mgr._mappings_loaded is False

    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    mgr.load_repository_mappings(repo)
    assert mgr._mappings_loaded is True

    # Modify map manually to verify second call returns cached dictionary
    mgr.image_map["TEST_CACHE"] = "cached_path"
    img_map_2, _ = mgr.load_repository_mappings(repo)

    assert "TEST_CACHE" in img_map_2


def test_missing_file_media_processing() -> None:
    """Test handling of missing or corrupted media files gracefully."""
    mgr = MediaManager()
    msg = {
        "message_id": "MSG_MISSING_TEST",
        "media_type": "image",
        "media_id": "img_non_existent",
        "file_path": "dataset/media/images/non_existent_file.png",
    }

    res = mgr.process_media(msg)
    assert res is not None
    assert res.processed is False
    assert res.classification == "Unknown"
