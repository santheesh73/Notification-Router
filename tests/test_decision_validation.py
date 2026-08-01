"""Unit tests for DecisionValidator."""

from src.confidence.validation import DecisionValidator


def test_reason_truncation_to_25_words() -> None:
    """Test DecisionValidator truncating long reasons to 25 words."""
    validator = DecisionValidator()
    long_reason = "This is a very long explanation that has more than twenty five words in total to test whether the validator will properly truncate it down to twenty five words as required by specifications."

    clean_reason = validator.validate_reason(long_reason)
    words = clean_reason.split()

    assert len(words) <= 25
    assert "```json" not in clean_reason


def test_evidence_id_deduplication() -> None:
    """Test deduplicating evidence message IDs."""
    validator = DecisionValidator()
    raw_ev = ["MH_001", "MH_002", "MH_001", "none", "MH_003"]

    clean_ev = validator.validate_evidence_ids(raw_ev)
    assert clean_ev == ["MH_001", "MH_002", "MH_003"]
