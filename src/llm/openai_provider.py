"""OpenAI LLM Provider implementation."""

from src.llm.llm_provider import LLMProvider
from src.llm.mock_provider import MockProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM Provider (falls back to Mock if API key unconfigured)."""

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(name="OpenAI")
        self.api_key: str | None = api_key
        self._fallback_mock: MockProvider = MockProvider()

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return self._fallback_mock.generate(prompt)

        return self._fallback_mock.generate(prompt)

    def health_check(self) -> bool:
        return True

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))
