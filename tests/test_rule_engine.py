"""Unit tests for NotificationRuleEngine and RulePipeline."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.rules.rule_engine import NotificationRuleEngine
from src.rules.rule_pipeline import RulePipeline, RuleValidationReport
from src.rules.rule_result import RuleResult


def test_rule_engine_routing() -> None:
    """Test routing message through rule engine."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    engine = NotificationRuleEngine()

    # 1. Urgent Message
    u_msg = {"message_id": "M_URG", "text_content": "EMERGENCY: Urgent hospital help needed!"}
    u_vec = feature_pipe.process(u_msg)
    u_res = engine.route(u_vec, ctx)
    assert u_res.resolved is True
    assert u_res.action == "notify"
    assert u_res.triggered_rule == "UrgentRule"

    # 2. Unresolved Ambiguous Message
    unres_msg = {"message_id": "M_AMBIG", "sender_id": "USR_999", "text_content": "Random neutral phrase here"}
    unres_vec = feature_pipe.process(unres_msg)
    unres_res = engine.route(unres_vec, ctx)
    assert unres_res.resolved is False
    assert unres_res.requires_ai is True
    assert unres_res.action == "unresolved"


def test_rule_pipeline_batch() -> None:
    """Test batch routing and pipeline summary report."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    msgs_df = repo.get_dataframe("messages")
    vectors = feature_pipe.process_dataset(msgs_df)

    rule_pipe = RulePipeline()
    results = rule_pipe.route_batch(vectors, ctx)

    assert len(results) == len(vectors)
    report = rule_pipe.validate(results)
    assert isinstance(report, RuleValidationReport)
    assert report.is_valid is True

    summary_str = rule_pipe.summary(results)
    assert "Total Messages Routed" in summary_str
    assert "Messages Resolved" in summary_str
