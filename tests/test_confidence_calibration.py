"""Unit tests for ConfidenceEngine and ConfidenceCalibrator."""

import pandas as pd

from config.settings import DATASET_PATH, OUTPUT_CSV_PATH
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
    conf = engine.compute_confidence(rule_res, llm_res, retrieval_result=None, media_result=None, vector=vec, action="notify", message_type="payment")

    assert isinstance(conf, float)
    assert 0.45 <= conf <= 0.99


def test_confidence_distribution_and_digest_calibration() -> None:
    """SECTION 2 Unit Test: Assert std > 0.10 and digest mean confidence < scam/mute mean confidence."""
    if not OUTPUT_CSV_PATH.exists():
        return

    df = pd.read_csv(OUTPUT_CSV_PATH)
    std_val = float(df["confidence"].std())

    # 1. Assert confidence distribution has realistic spread (std > 0.10)
    assert std_val > 0.10, f"Confidence std={std_val:.4f} is too flat (expected > 0.10)!"

    # 2. Assert mean confidence for action == 'digest' is lower than rule-resolved scam/spam rows
    digest_mean = float(df[df["action"] == "digest"]["confidence"].mean())
    scam_spam_mean = float(df[df["message_type"].isin(["scam", "spam"])]["confidence"].mean())

    assert digest_mean < scam_spam_mean - 0.15, (
        f"Digest mean confidence ({digest_mean:.4f}) is not meaningfully lower than "
        f"scam/spam mean confidence ({scam_spam_mean:.4f})!"
    )
