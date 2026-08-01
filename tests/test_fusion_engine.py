"""Unit tests for DecisionFusionEngine."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.final_decision import FinalDecision
from src.confidence.fusion_engine import DecisionFusionEngine, FusionValidationReport
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.decision_result import DecisionResult
from src.rules.rule_result import RuleResult


def test_fusion_engine_single_message() -> None:
    """Test fusing signals for a single message."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "MSG_FUSE", "sender_id": "USR_101", "text_content": "Coffee meeting today"}
    vec = feature_pipe.process(msg)

    rule_res = RuleResult("MSG_FUSE", True, "digest", "event", "Scheduled meeting", 0.85, "EventRule", "3", False)
    llm_res = DecisionResult("MSG_FUSE", "digest", "event", "Scheduled meeting", 0.85)

    engine = DecisionFusionEngine()
    final_dec = engine.fuse_decision(
        vector=vec,
        rule_result=rule_res,
        llm_result=llm_res,
        media_result=None,
        retrieval_result=None,
        context=ctx,
    )

    assert isinstance(final_dec, FinalDecision)
    assert final_dec.message_id == "MSG_FUSE"
    assert final_dec.action == "digest"
    assert final_dec.decision_source == "RULE_ENGINE"
    assert 0.0 <= final_dec.confidence <= 1.0


def test_fusion_engine_batch() -> None:
    """Test batch fusion processing and summary generation."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    msgs_df = repo.get_dataframe("messages")
    vectors = feature_pipe.process_dataset(msgs_df)

    rule_results = [
        RuleResult("MSG_001", True, "digest", "event", "Meeting", 0.85, "EventRule", "3", False),
        RuleResult("MSG_002", False, "unresolved", "unknown", "None", 0.0, "None", "4", True),
        RuleResult("MSG_003", True, "notify", "office", "Work", 0.90, "OfficeRule", "2", False),
        RuleResult("MSG_004", False, "unresolved", "unknown", "None", 0.0, "None", "4", True),
        RuleResult("MSG_005", True, "notify", "family", "Family", 0.91, "FamilyRule", "2", False),
    ]

    llm_results = [
        DecisionResult("MSG_001", "digest", "event", "Meeting", 0.85, provider="RuleEngine"),
        DecisionResult("MSG_002", "notify", "personal", "Personal DM", 0.82, provider="Mock"),
        DecisionResult("MSG_003", "notify", "office", "Work", 0.90, provider="RuleEngine"),
        DecisionResult("MSG_004", "notify", "payment", "Payment reminder", 0.87, provider="Mock"),
        DecisionResult("MSG_005", "notify", "family", "Family", 0.91, provider="RuleEngine"),
    ]

    engine = DecisionFusionEngine()
    final_decisions = engine.fuse_batch(
        vectors=vectors,
        rule_results=rule_results,
        llm_results=llm_results,
        context=ctx,
    )

    assert len(final_decisions) == len(vectors)

    report = engine.validate(final_decisions)
    assert isinstance(report, FusionValidationReport)
    assert report.is_valid is True

    summary_str = engine.summary(final_decisions)
    assert "Total Final Decisions" in summary_str
    assert "Average Calibrated Confidence" in summary_str
