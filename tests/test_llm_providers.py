"""Unit tests for concrete LLM Providers."""

from src.llm.gemini_provider import GeminiProvider
from src.llm.mock_provider import MockProvider
from src.llm.openai_provider import OpenAIProvider


def test_mock_provider() -> None:
    """Test MockProvider generation."""
    provider = MockProvider()
    assert provider.health_check() is True

    out = provider.generate("payment prompt")
    assert "notify" in out or "digest" in out
    assert provider.count_tokens("hello world") == 2


def test_gemini_provider_fallback() -> None:
    """Test GeminiProvider fallback when unconfigured."""
    provider = GeminiProvider(api_key=None)
    assert provider.health_check() is True

    out = provider.generate("test prompt")
    assert isinstance(out, str)


def test_openai_provider_fallback() -> None:
    """Test OpenAIProvider fallback when unconfigured."""
    provider = OpenAIProvider(api_key=None)
    assert provider.health_check() is True

    out = provider.generate("test prompt")
    assert isinstance(out, str)
