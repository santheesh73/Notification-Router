"""Abstract Base Feature Extractor."""

from abc import ABC, abstractmethod
from typing import Any

from src.builders.context_manager import ContextManager


class BaseFeatureExtractor(ABC):
    """Abstract base class for all domain-specific feature extractors."""

    @abstractmethod
    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract a dictionary of feature signals from a message and context layer.

        Args:
            message: Raw message dictionary or record.
            context: ContextManager instance.

        Returns:
            Dictionary mapping feature names to extracted signal values.
        """
        pass
