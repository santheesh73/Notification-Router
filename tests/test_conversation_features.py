"""Unit tests for ConversationFeatureExtractor."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.conversation_features import ConversationFeatureExtractor
from src.loaders.load_data import DataRepository


def test_conversation_feature_extraction() -> None:
    """Test group, personal, and business conversation classification."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    extractor = ConversationFeatureExtractor()

    grp_msg = {"sender_id": "USR_101", "group_id": "GRP_501", "message_type": "text"}
    feats_g = extractor.extract(grp_msg, ctx)
    assert feats_g["group"] is True
    assert feats_g["conversation_type"] == "group"

    biz_msg = {"sender_id": "BUS_301", "message_type": "text"}
    feats_b = extractor.extract(biz_msg, ctx)
    assert feats_b["business"] is True
    assert feats_b["conversation_type"] == "business"

    direct_msg = {"sender_id": "USR_101", "recipient_id": "USR_102", "message_type": "image", "has_media": True}
    feats_d = extractor.extract(direct_msg, ctx)
    assert feats_d["personal"] is True
    assert feats_d["has_media"] is True
