"""Unit tests for Phase 11 Optimization module."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.final_decision import FinalDecision
from src.evaluation.benchmark import BenchmarkReport
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.optimization.cache_optimizer import CacheOptimizer
from src.optimization.confidence_optimizer import AdaptiveConfidenceOptimizer
from src.optimization.evaluator import OptimizationEvaluator
from src.optimization.optimizer import SystemOptimizer
from src.optimization.prompt_optimizer import PromptOptimizer
from src.optimization.retrieval_optimizer import RetrievalOptimizer
from src.optimization.rule_optimizer import RuleOptimizer
from src.rules.rule_result import RuleResult


def test_rule_optimizer() -> None:
    """Test RuleOptimizer analysis."""
    rule_results = [
        RuleResult("M1", True, "notify", "payment", "Reason", 0.95, "PaymentRule", "2", False),
    ]
    optimizer = RuleOptimizer()
    report = optimizer.analyze_rule_performance(rule_results)

    assert report.total_rules_evaluated == 15
    assert "PaymentRule" in report.active_rules


def test_prompt_optimizer() -> None:
    """Test PromptOptimizer context compaction."""
    optimizer = PromptOptimizer()
    raw_prompt = "Line 1\n\n  Line 2  \n\nLine 3"
    compact, metrics = optimizer.optimize_prompt_string(raw_prompt)

    assert "Line 1\nLine 2\nLine 3" in compact
    assert metrics.character_length > 0


def test_adaptive_confidence_optimizer() -> None:
    """Test AdaptiveConfidenceOptimizer calibration."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_OPT", "sender_id": "BUS_301", "text_content": "Payment notice"}
    vec = feature_pipe.process(msg)

    optimizer = AdaptiveConfidenceOptimizer()
    conf = optimizer.optimize_confidence(0.85, vec, evidence_count=3)

    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0


def test_system_optimizer_run(tmp_path: Path) -> None:
    """Test SystemOptimizer master run generating leaderboard reports."""
    optimizer = SystemOptimizer(reports_dir=tmp_path)
    decisions = [
        FinalDecision("M1", "notify", "payment", "Reason", 0.90, ["E1"], decision_source="RULE_ENGINE"),
    ]
    rule_results = [
        RuleResult("M1", True, "notify", "payment", "Reason", 0.90, "PaymentRule", "2", False),
    ]
    benchmark = BenchmarkReport(total_messages=1, messages_per_second=50.0)

    audit_dict = optimizer.run_optimization(decisions, rule_results, benchmark)

    assert audit_dict["quality_score"] == 100.0
    assert (tmp_path / "quality_audit.md").exists()
    assert (tmp_path / "submission_checklist.md").exists()
    assert (tmp_path / "leaderboard_report.md").exists()
    assert (tmp_path / "optimization_report.json").exists()
    assert (tmp_path / "performance_report.json").exists()
