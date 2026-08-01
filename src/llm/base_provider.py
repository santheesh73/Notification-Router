"""Abstract Base Provider for LLM Integrations."""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract Base Class for all LLM Providers (Groq, Gemma, Mock)."""

    def __init__(self, provider_name: str, model_name: str) -> None:
        """Initialize base provider.

        Args:
            provider_name: Canonical name of provider.
            model_name: Configured model identifier.
        """
        self.provider_name: str = provider_name
        self.model_name: str = model_name

    @abstractmethod
    def generate(self, prompt: str, timeout: float = 15.0) -> dict[str, Any]:
        """Generate response for a single text prompt.

        Args:
            prompt: Text prompt string.
            timeout: Generation timeout in seconds.

        Returns:
            Dictionary containing 'raw_text', 'latency', 'provider', 'model', 'tokens'.
        """
        pass

    @abstractmethod
    def generate_batch(self, prompts: list[str], timeout: float = 30.0) -> list[dict[str, Any]]:
        """Generate responses for a batch of text prompts.

        Args:
            prompts: List of text prompt strings.
            timeout: Batch generation timeout in seconds.

        Returns:
            List of response dictionaries matching generate() structure.
        """
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check provider connectivity, credentials, and API health.

        Returns:
            True if healthy and ready for inference, else False.
        """
        pass
