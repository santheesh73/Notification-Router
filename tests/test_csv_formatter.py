"""Unit tests for CSVFormatter."""

from src.confidence.final_decision import FinalDecision
from src.output.csv_formatter import CSVFormatter


def test_csv_formatter() -> None:
    """Test CSVFormatter converts FinalDecision into CSV dictionary."""
    formatter = CSVFormatter()
    dec = FinalDecision(
        message_id="MSG_001",
        action="notify",
        message_type="payment",
        reason="Trusted payment reminder.",
        confidence=0.94,
        evidence_message_ids=["MH_001", "MH_002"],
    )

    formatted = formatter.format_decision(dec)

    assert formatted["message_id"] == "MSG_001"
    assert formatted["action"] == "notify"
    assert formatted["message_type"] == "payment"
    assert formatted["confidence"] == 0.94
    assert formatted["evidence_message_ids"] == "MH_001;MH_002"
