"""Unit tests for OutputValidator."""

from pathlib import Path

from src.output.output_validator import OutputValidator


def test_output_validator_valid_csv(tmp_path: Path) -> None:
    """Test validating valid output.csv file."""
    output_file = tmp_path / "output.csv"
    content = "message_id,action,message_type,reason,confidence,evidence_message_ids\nMSG1,notify,payment,Valid,0.90,MH1\nMSG2,digest,event,Valid,0.80,none\n"
    output_file.write_text(content, encoding="utf-8")

    validator = OutputValidator()
    report = validator.validate_csv(output_file, expected_row_count=2)

    assert report.is_valid is True
    assert report.total_rows == 2
