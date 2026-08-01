"""Abstract Base LLM Provider Interface & Factory."""

from abc import ABC, abstractmethod
import os

from dotenv import load_dotenv

from src.utils.logger import logger

load_dotenv()


class LLMProvider(ABC):
    """Abstract interface for pluggable LLM provider implementations."""

    def __init__(self, name: str) -> None:
        """Initialize LLMProvider.

        Args:
            name: Provider name identifier.
        """
        self.name: str = name

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate textual completion from prompt.

        Args:
            prompt: Text prompt string.

        Returns:
            Generated response string (raw JSON).
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check provider health and readiness.

        Returns:
            True if provider is reachable and active, else False.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for input text string.

        Args:
            text: Input text string.

        Returns:
            Estimated token count integer.
        """
        pass


def get_provider(requested_provider: str | None = None) -> LLMProvider:
    """Factory creating LLMProvider based on environment configuration.

    Priority:
    1. Groq
    2. Mock (Development Fallback)

    Args:
        requested_provider: Optional explicit provider name string.

    Returns:
        LLMProvider instance.
    """
    load_dotenv()

    from src.llm.mock_provider import MockProvider

    prov_env = (requested_provider or os.getenv("MODEL_PROVIDER", "groq")).lower().strip()

    if prov_env == "mock":
        logger.info("Mock Provider Initialized (Development Mode)")
        return MockProvider()

    # Default: Mock provider for legacy DecisionOrchestrator path
    # The production Hybrid Multi-LLM Router (Groq -> Gemma -> Rule) handles all real LLM routing
    logger.info("Mock Provider Initialized for legacy orchestrator compatibility")
    return MockProvider()
