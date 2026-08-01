"""Unit tests for DecisionOrchestrator and LLMRouter."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.decision_result import DecisionResult
from src.llm.llm_router import DecisionValidationReport, LLMRouter
from src.llm.orchestrator import DecisionOrchestrator
from src.rules.rule_result import RuleResult


def test_orchestrator_resolved_rule_skips_llm() -> None:
    """Test DecisionOrchestrator skipping LLM for resolved rule."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_RESOLVED", "sender_id": "USR_101", "text_content": "Resolved"}
    vec = feature_pipe.process(msg)
    rule_res = RuleResult(
        message_id="M_RESOLVED",
        resolved=True,
        action="notify",
        message_type="urgent",
        reason="Urgent hospital alert",
        confidence=0.99,
        triggered_rule="UrgentRule",
        priority="1",
        requires_ai=False,
    )

    orchestrator = DecisionOrchestrator()
    dec = orchestrator.process_message(vec, rule_res, ctx)

    assert dec.action == "notify"
    assert dec.provider == "RuleEngine"
    assert dec.tokens["total_tokens"] == 0


def test_orchestrator_unresolved_rule_invokes_llm() -> None:
    """Test DecisionOrchestrator invoking LLM for unresolved rule."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_UNRESOLVED", "sender_id": "USR_101", "text_content": "Ambiguous message"}
    vec = feature_pipe.process(msg)
    rule_res = RuleResult(
        message_id="M_UNRESOLVED",
        resolved=False,
        action="unresolved",
        message_type="unknown",
        reason="No rule matched",
        confidence=0.0,
        triggered_rule="None",
        priority="4",
        requires_ai=True,
    )

    orchestrator = DecisionOrchestrator()
    dec = orchestrator.process_message(vec, rule_res, ctx)

    assert isinstance(dec, DecisionResult)
    assert dec.provider in ["Gemini", "Mock", "OpenAI"]
    assert dec.tokens["total_tokens"] > 0


def test_llm_router_batch() -> None:
    """Test LLMRouter batch execution and summary reporting."""
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

    router = LLMRouter()
    decisions = router.process_batch(vectors, rule_results, ctx)

    assert len(decisions) == len(vectors)

    report = router.validate(decisions)
    assert isinstance(report, DecisionValidationReport)
    assert report.is_valid is True

    summary_str = router.summary(decisions)
    assert "Total Messages Evaluated" in summary_str
    assert "Rule Engine" in summary_str
    assert "Messages Sent to LLM (Unresolved)" in summary_str
