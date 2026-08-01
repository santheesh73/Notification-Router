"""Unit tests for CSVFormatter and Reason Uniqueness."""

import pandas as pd

from config.settings import OUTPUT_CSV_PATH
from src.confidence.final_decision import FinalDecision
from src.output.csv_formatter import CSVFormatter


def test_csv_formatter() -> None:
    """Test CSVFormatter converts FinalDecision into CSV dictionary."""
    formatter = CSVFormatter()
    dec = FinalDecision(
        message_id="MSG_001",
        action="notify",
        message_type="payment",
        reason="Trusted payment reminder for MSG_001.",
        confidence=0.94,
        evidence_message_ids=["MH_001", "MH_002"],
    )

    formatted = formatter.format_decision(dec)

    assert formatted["message_id"] == "MSG_001"
    assert formatted["action"] == "notify"
    assert formatted["message_type"] == "payment"
    assert formatted["confidence"] == 0.94
    assert formatted["evidence_message_ids"] == "MH_001;MH_002"


def test_reason_uniqueness_and_grounding() -> None:
    """SECTION 3 Unit Test: Assert reason uniqueness ratio > 0.50 and no generic reason dominates > 5%."""
    if not OUTPUT_CSV_PATH.exists():
        return

    df = pd.read_csv(OUTPUT_CSV_PATH)
    total_rows = len(df)
    unique_reasons = df["reason"].nunique()
    uniqueness_ratio = unique_reasons / total_rows

    # 1. Assert reason uniqueness ratio > 0.50
    assert uniqueness_ratio > 0.50, f"Reason uniqueness ratio={uniqueness_ratio:.2f} is too low (expected > 0.50)!"

    # 2. Assert no single reason appears more than 5% of the time (max frequency <= 5% of 110 = 5.5 occurrences)
    top_reason_count = df["reason"].value_counts().max()
    max_allowed = max(5, int(total_rows * 0.05))

    assert top_reason_count <= max_allowed, (
        f"Top reason string appears {top_reason_count} times (> 5% threshold of {max_allowed})! "
        f"Reasons must be entity-grounded."
    )
