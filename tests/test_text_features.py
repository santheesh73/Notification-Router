"""Unit tests for TextFeatureExtractor."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.text_features import TextFeatureExtractor
from src.loaders.load_data import DataRepository


def test_text_feature_extraction() -> None:
    """Test text feature extraction signals."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    extractor = TextFeatureExtractor()
    sample_msg = {
        "message_id": "M1",
        "text_content": "URGENT: Please pay invoice #9812 of $150 via http://pay.com before 5:00 PM!",
    }

    feats = extractor.extract(sample_msg, ctx)

    assert feats["contains_payment"] is True
    assert feats["contains_invoice"] is True
    assert feats["contains_url"] is True
    assert feats["contains_money"] is True
    assert feats["contains_deadline"] is True
    assert feats["uppercase_ratio"] > 0.0
    assert feats["word_count"] > 5
