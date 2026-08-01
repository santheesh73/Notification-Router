"""Unit tests for TemporalFeatureExtractor."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.temporal_features import TemporalFeatureExtractor
from src.loaders.load_data import DataRepository


def test_temporal_feature_extraction() -> None:
    """Test date and time parsing and quiet hours checks."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    extractor = TemporalFeatureExtractor()
    sample_msg = {
        "message_id": "M_TIME",
        "recipient_id": "USR_101",
        "timestamp": "2026-08-01 23:30:00",
    }

    feats = extractor.extract(sample_msg, ctx)

    assert feats["hour_of_day"] == 23
    assert feats["night"] is True
    assert isinstance(feats["during_quiet_hours"], bool)
