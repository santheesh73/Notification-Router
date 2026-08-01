"""Abstract Base Context Builder."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import pandas as pd

from src.loaders.load_data import DataRepository
from src.utils.logger import logger

T = TypeVar("T")


class BaseContextBuilder(ABC, Generic[T]):
    """Abstract base class for all context profile builders."""

    def __init__(self, repository: DataRepository) -> None:
        """Initialize builder with data repository dependency injection.

        Args:
            repository: Loaded DataRepository instance.
        """
        self.repository: DataRepository = repository
        self._cache: dict[str, T] = {}

    def get_dataset(self, name: str) -> pd.DataFrame:
        """Helper method to safely retrieve DataFrame from repository.

        Args:
            name: Dataset name.

        Returns:
            pandas DataFrame.
        """
        try:
            return self.repository.get_dataframe(name)
        except Exception as exc:
            logger.warning(f"Builder could not load dataset '{name}': {exc}")
            return pd.DataFrame()

    @abstractmethod
    def build(self) -> dict[str, T]:
        """Build and return context profiles dictionary.

        Returns:
            Dictionary mapping primary key IDs to profile objects.
        """
        pass
