"""Unit tests for ExecutionPipeline."""

from pathlib import Path

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.confidence.final_decision import FinalDecision
from src.loaders.load_data import DataRepository
from src.output.output_writer import OutputWriter
from src.pipeline.execution_pipeline import ExecutionPipeline


def test_execution_pipeline_run(tmp_path: Path) -> None:
    """Test full pipeline run emitting output CSV."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    out_file = tmp_path / "output.csv"
    writer = OutputWriter(output_path=out_file)

    pipeline = ExecutionPipeline(
        repository=repo,
        context=ctx,
        batch_size=5,
        checkpoint_interval=2,
        output_writer=writer,
    )

    decisions = pipeline.run(resume=False, overwrite_output=True)
    expected_len = len(repo.get_dataframe("messages"))

    assert len(decisions) == expected_len
    assert out_file.exists()

    lines = out_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == expected_len + 1  # Header + message rows
