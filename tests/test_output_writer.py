"""Unit tests for OutputWriter."""

from pathlib import Path

from src.confidence.final_decision import FinalDecision
from src.output.output_writer import OutputWriter


def test_output_writer_incremental(tmp_path: Path) -> None:
    """Test incremental CSV writing and header creation."""
    output_file = tmp_path / "output.csv"
    writer = OutputWriter(output_path=output_file)

    dec1 = FinalDecision("M1", "notify", "payment", "Reason 1", 0.90, ["E1"])
    dec2 = FinalDecision("M2", "digest", "event", "Reason 2", 0.80, ["E2"])

    writer.write_row(dec1)
    writer.write_row(dec2)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().splitlines()

    assert len(lines) == 3  # Header + 2 rows
    assert "message_id,action,message_type,reason,confidence,evidence_message_ids" in lines[0]
    assert "M1,notify,payment" in lines[1]
    assert "M2,digest,event" in lines[2]
