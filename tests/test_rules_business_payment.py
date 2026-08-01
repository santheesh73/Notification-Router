"""Unit tests for BusinessRule and PaymentRule."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.business_rule import BusinessRule
from src.rules.payment_rule import PaymentRule


def test_payment_rule() -> None:
    """Test PaymentRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_PAY_TEST",
        "sender_id": "BUS_301",
        "text_content": "Payment receipt for Invoice #9812 paid successfully via UPI.",
    }
    vec = pipeline.process(msg)

    rule = PaymentRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.resolved is True
    assert res.action == "notify"
    assert res.message_type == "payment"
    assert res.confidence == 0.93


def test_business_rule() -> None:
    """Test BusinessRule trigger conditions."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    pipeline = FeaturePipeline(ctx)

    msg = {
        "message_id": "M_BIZ_TEST",
        "sender_id": "BUS_301",
        "text_content": "Your order #9812 has been shipped and is out for delivery today.",
    }
    vec = pipeline.process(msg)

    rule = BusinessRule()
    res = rule.evaluate(vec, ctx)

    assert res is not None
    assert res.resolved is True
    assert res.action in ["notify", "digest"]
    assert res.message_type in ["business", "business_update"]
