"""Unit tests for PromptBuilder."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.prompt_builder import PromptBuilder
from src.rules.rule_result import RuleResult


def test_prompt_builder() -> None:
    """Test prompt construction with structured facts."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_P_TEST", "sender_id": "USR_101", "text_content": "Random phrase"}
    vec = feature_pipe.process(msg)
    rule_res = RuleResult(
        message_id="M_P_TEST",
        resolved=False,
        action="unresolved",
        message_type="unknown",
        reason="None",
        confidence=0.0,
        triggered_rule="None",
        priority="4",
        requires_ai=True,
    )

    builder = PromptBuilder()
    prompt = builder.build_prompt(vec, rule_res, media_result=None, retrieval_result=None, context=ctx)

    assert "SYSTEM ROLE" in prompt
    assert "M_P_TEST" in prompt
    assert "FEATURE VECTOR FACTS" in prompt
    assert "DECISION INSTRUCTIONS" in prompt
