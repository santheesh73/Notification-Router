"""Unit tests for ScamRule and UrgentRule."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.scam_rule import ScamRule
from src.rules.urgent_rule import UrgentRule


def test_scam_rule() -> None:
    """Test ScamRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_SCAM_TEST",
        "sender_id": "USR_999",
        "text_content": "CONGRATULATIONS! You won $10,000 lottery! Click bit.ly/claim to verify.",
    }
    vec = pipeline.process(msg)

    rule = ScamRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.resolved is True
    assert res.action == "mute"
    assert res.message_type == "scam"
    assert res.confidence >= 0.95


def test_urgent_rule() -> None:
    """Test UrgentRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_URGENT_TEST",
        "sender_id": "USR_101",
        "text_content": "EMERGENCY: Urgent assistance needed at hospital ASAP!",
    }
    vec = pipeline.process(msg)

    rule = UrgentRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.resolved is True
    assert res.action == "notify"
    assert res.message_type == "urgent"
    assert res.confidence == 0.99
