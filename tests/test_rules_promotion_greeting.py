"""Unit tests for PromotionRule and GreetingRule."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.greeting_rule import GreetingRule
from src.rules.promotion_rule import PromotionRule


def test_promotion_rule() -> None:
    """Test PromotionRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_PROMO_TEST",
        "sender_id": "BUS_303",
        "text_content": "Get 50% discount on all pizza orders with coupon SAVE50 today!",
    }
    vec = pipeline.process(msg)

    rule = PromotionRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.action in ["digest", "mute"]
    assert res.message_type == "promotion"


def test_greeting_rule() -> None:
    """Test GreetingRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_GREET_TEST",
        "sender_id": "USR_102",
        "text_content": "Good morning! Wishing you a fantastic day ahead.",
    }
    vec = pipeline.process(msg)

    rule = GreetingRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.action == "digest"
    assert res.message_type == "greeting"
    assert res.confidence >= 0.85
