"""Unit tests for ConfidenceEngine and ConfidenceCalibrator."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.confidence_engine import ConfidenceEngine
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.decision_result import DecisionResult
from src.rules.rule_result import RuleResult


def test_confidence_calibration_bounds() -> None:
    """Test confidence engine clamping output in range [0.0, 1.0]."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_CONF_TEST", "sender_id": "BUS_301", "text_content": "Invoice payment"}
    vec = feature_pipe.process(msg)

    rule_res = RuleResult("M_CONF_TEST", True, "notify", "payment", "Payment", 0.95, "PaymentRule", "2", False)
    llm_res = DecisionResult("M_CONF_TEST", "notify", "payment", "Payment", 0.90)

    engine = ConfidenceEngine()
    conf = engine.compute_confidence(rule_res, llm_res, retrieval_result=None, media_result=None, vector=vec, action="notify")

    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
