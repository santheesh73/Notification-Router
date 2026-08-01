"""Unit tests for ResponseParser and ResponseValidator."""

from src.llm.response_parser import ResponseParser
from src.llm.response_validator import ResponseValidator


def test_response_parser_valid_json() -> None:
    """Test ResponseParser parsing valid JSON."""
    parser = ResponseParser()
    raw = '```json\n{"action": "notify", "message_type": "payment", "reason": "Payment reminder", "confidence": 0.90}\n```'
    parsed = parser.parse(raw)

    assert parsed["action"] == "notify"
    assert parsed["confidence"] == 0.90


def test_response_validator() -> None:
    """Test ResponseValidator checking required fields and enums."""
    validator = ResponseValidator()

    # Valid
    v1, err1 = validator.validate({"action": "notify", "message_type": "payment", "reason": "Valid reason", "confidence": 0.85})
    assert v1 is True
    assert err1 == "Valid"

    # Invalid Action
    v2, err2 = validator.validate({"action": "invalid_action", "message_type": "payment", "reason": "Valid", "confidence": 0.85})
    assert v2 is False
    assert "Invalid action" in err2

    # Invalid Confidence out of bounds
    v3, err3 = validator.validate({"action": "notify", "message_type": "payment", "reason": "Valid", "confidence": 1.5})
    assert v3 is False
    assert "out of bounds" in err3
