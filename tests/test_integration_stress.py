"""Integration and Stress Testing Suite."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.final_decision import FinalDecision
from src.confidence.fusion_engine import DecisionFusionEngine
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.output.output_writer import OutputWriter
from src.rules.rule_engine import NotificationRuleEngine


def test_pipeline_batch_stress_100_messages(tmp_path: Path) -> None:
    """Stress test routing 100 dynamically generated messages."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    rule_engine = NotificationRuleEngine()
    fusion_engine = DecisionFusionEngine()

    output_file = tmp_path / "stress_output.csv"
    writer = OutputWriter(output_path=output_file)

    for i in range(100):
        msg = {
            "message_id": f"MSG_STRESS_{i:03d}",
            "sender_id": "USR_101" if i % 2 == 0 else "BUS_301",
            "text_content": f"Stress message payload number {i} regarding meeting and payment.",
        }
        vec = feature_pipe.process(msg)
        rule_res = rule_engine.route(vec, ctx)

        final_dec = fusion_engine.fuse_decision(
            vector=vec,
            rule_result=rule_res,
            llm_result=None,
            media_result=None,
            retrieval_result=None,
            context=ctx,
        )
        writer.write_row(final_dec)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 101  # Header + 100 rows


def test_output_writer_append_consistency(tmp_path: Path) -> None:
    """Test output writer append consistency under rapid successive writes."""
    output_file = tmp_path / "rapid_output.csv"
    writer = OutputWriter(output_path=output_file)

    decisions = [
        FinalDecision(f"M_{i}", "notify", "payment", f"Reason {i}", 0.90, ["E1"])
        for i in range(50)
    ]

    for d in decisions:
        writer.write_row(d)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 51
