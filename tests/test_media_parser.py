"""Unit tests for ImageParser and TranscriptParser."""

from src.media.image.image_parser import ImageParser
from src.media.voice.transcript_parser import TranscriptParser


def test_image_parser() -> None:
    """Test image JSON output parsing."""
    parser = ImageParser()
    raw = {
        "classification": "Invoice",
        "summary": "Monthly cloud invoice.",
        "amounts": ["$50.00"],
        "dates": ["2026-08-01"],
        "confidence": 0.96,
    }
    parsed = parser.parse(raw)

    assert parsed["classification"] == "Invoice"
    assert parsed["amounts"] == ["$50.00"]
    assert parsed["confidence"] == 0.96


def test_transcript_parser() -> None:
    """Test transcript text parsing."""
    parser = TranscriptParser()
    raw = {"text": "Urgent emergency hospital visit needed tomorrow at 5 PM", "confidence": 0.95}
    parsed = parser.parse(raw)

    assert parsed["classification"] == "Emergency"
    assert parsed["urgency"] == "high"
    assert "tomorrow" in parsed["dates"]
