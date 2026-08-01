"""Edge Case & Error Handling Unit Tests."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.fusion_engine import DecisionFusionEngine
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.media.media_manager import MediaManager
from src.rules.rule_engine import NotificationRuleEngine


def test_missing_text_empty_message() -> None:
    """Test feature extraction and rule routing for empty message text."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    rule_engine = NotificationRuleEngine()

    empty_msg = {"message_id": "M_EMPTY", "sender_id": "USR_101", "text_content": ""}
    vec = feature_pipe.process(empty_msg)

    assert vec.message_length == 0
    assert vec.word_count == 0

    rule_res = rule_engine.route(vec, ctx)
    assert rule_res is not None


def test_only_emojis_message() -> None:
    """Test feature extraction for message containing only emojis."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    emoji_msg = {"message_id": "M_EMOJI", "sender_id": "USR_101", "text_content": "😀😁😂🤣🤣🔥🔥"}
    vec = feature_pipe.process(emoji_msg)

    assert vec.message_length > 0


def test_very_long_message() -> None:
    """Test feature extraction for very long message (>10,000 chars)."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    long_text = "Important work update. " * 500
    long_msg = {"message_id": "M_LONG", "sender_id": "USR_101", "text_content": long_text}
    vec = feature_pipe.process(long_msg)

    assert vec.message_length > 10000
    assert vec.word_count > 1000


def test_very_high_forwarded_count() -> None:
    """Test feature extraction for message with high forwarded count."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    fwd_msg = {
        "message_id": "M_FWD",
        "sender_id": "USR_101",
        "text_content": "Forwarded many times",
        "forwarded_count": 150,
        "is_forwarded": True,
    }
    vec = feature_pipe.process(fwd_msg)

    assert vec.forwarded_count == 150
    assert vec.is_forwarded is True


def test_unknown_sender_and_business() -> None:
    """Test context retrieval for unknown sender and business IDs."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    user_prof = ctx.get_user("USR_NON_EXISTENT")
    assert user_prof is None

    biz_prof = ctx.get_business("BUS_NON_EXISTENT")
    assert biz_prof is None


def test_missing_media_file() -> None:
    """Test MediaManager handling missing media file path safely."""
    media_mgr = MediaManager()
    msg = {"message_id": "M_MISSING_MEDIA", "media_type": "image", "media_file": "non_existent_file.png"}

    m_res = media_mgr.process_media(msg)
    assert m_res is not None
    assert m_res.media_type in ["image", "none"]
    assert m_res.processed is False
