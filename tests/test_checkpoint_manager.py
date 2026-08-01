"""Unit tests for CheckpointManager."""

from pathlib import Path

from src.pipeline.checkpoint_manager import CheckpointManager


def test_checkpoint_save_and_load(tmp_path: Path) -> None:
    """Test CheckpointManager saving and resuming state."""
    ckpt_file = tmp_path / "checkpoint.json"
    manager = CheckpointManager(checkpoint_path=ckpt_file, interval=25)

    manager.save_checkpoint(last_processed_index=24, processed_ids=["MSG1", "MSG2"])

    assert ckpt_file.exists()

    last_idx, proc_set = manager.load_checkpoint()
    assert last_idx == 24
    assert "MSG1" in proc_set
    assert "MSG2" in proc_set

    manager.clear_checkpoint()
    assert not ckpt_file.exists()
