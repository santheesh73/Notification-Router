"""Unit tests for RetryHandler."""

from src.llm.llm_provider import LLMProvider
from src.llm.mock_provider import MockProvider
from src.llm.retry_handler import RetryHandler


class FailingProvider(LLMProvider):
    """Provider returning invalid output."""

    def __init__(self) -> None:
        super().__init__(name="Failing")

    def generate(self, prompt: str) -> str:
        return "invalid non-json text"

    def health_check(self) -> bool:
        return True

    def count_tokens(self, text: str) -> int:
        return 5


def test_retry_handler_success() -> None:
    """Test RetryHandler with valid provider."""
    handler = RetryHandler(max_retries=3)
    provider = MockProvider()

    res, attempts = handler.execute_with_retry(provider, "test prompt")
    assert isinstance(res, dict)
    assert res["action"] in ["notify", "digest", "mute"]
    assert attempts == 1


def test_retry_handler_fallback() -> None:
    """Test RetryHandler triggering fallback on failing provider."""
    handler = RetryHandler(max_retries=3)
    provider = FailingProvider()

    res, attempts = handler.execute_with_retry(provider, "test prompt")
    assert res["action"] == "digest"
    assert res["message_type"] == "unknown"
    assert res["confidence"] == 0.50
    assert attempts == 3
