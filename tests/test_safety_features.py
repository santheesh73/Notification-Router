"""Unit tests for SafetyFeatureExtractor."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.safety_features import SafetyFeatureExtractor
from src.loaders.load_data import DataRepository


def test_safety_feature_extraction() -> None:
    """Test scam, lottery, and risk score detection."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    extractor = SafetyFeatureExtractor()
    sample_scam = {
        "message_id": "M_SCAM",
        "text_content": "CONGRATULATIONS! You won $1,000,000 in our lottery! Click bit.ly/claim_now to verify your account immediately.",
    }

    feats = extractor.extract(sample_scam, ctx)

    assert feats["contains_scam_keyword"] is True
    assert feats["contains_lottery"] is True
    assert feats["contains_shortened_url"] is True
    assert feats["risk_score"] > 0.4
