"""Unit tests for ConflictResolver."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.conflict_resolver import ConflictResolver
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.rules.rule_result import RuleResult


def test_critical_rule_preserved() -> None:
    """Test Critical rule preservation."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_CRIT", "sender_id": "USR_999", "text_content": "CONGRATS! You won lottery click link."}
    vec = feature_pipe.process(msg)

    rule_res = RuleResult(
        message_id="M_CRIT",
        resolved=True,
        action="mute",
        message_type="scam",
        reason="Scam alert",
        confidence=0.98,
        triggered_rule="ScamRule",
        priority="RulePriority.CRITICAL",
        requires_ai=False,
    )
    llm_res = DecisionResult("M_CRIT", "notify", "personal", "LLM opinion", 0.80)

    resolver = ConflictResolver()
    act, m_type, reason, d_src, ai_res = resolver.resolve(rule_res, llm_res, media_result=None, vector=vec)

    assert act == "mute"
    assert m_type == "scam"
    assert d_src == "RULE_ENGINE"
    assert ai_res is False


def test_media_emergency_override() -> None:
    """Test Media Emergency signal overriding unresolved or digest rule."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_MED_EMERG", "sender_id": "USR_101", "text_content": "Check image attached"}
    vec = feature_pipe.process(msg)

    rule_res = RuleResult(
        message_id="M_MED_EMERG",
        resolved=False,
        action="unresolved",
        message_type="unknown",
        reason="None",
        confidence=0.0,
        triggered_rule="None",
        priority="4",
        requires_ai=True,
    )
    llm_res = DecisionResult("M_MED_EMERG", "digest", "event", "Event digest", 0.70)
    media_res = MediaResult("M_MED_EMERG", "image", True, "Emergency doctor note", "Emergency", urgency="critical")

    resolver = ConflictResolver()
    act, m_type, reason, d_src, ai_res = resolver.resolve(rule_res, llm_res, media_result=media_res, vector=vec)

    assert act == "notify"
    assert m_type == "urgent"
    assert d_src == "FUSED"
    assert ai_res is True
