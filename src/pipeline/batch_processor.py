"""Batch Processor for Chunked Execution."""

from typing import Any, Generator
import pandas as pd


class BatchProcessor:
    """Utility splitting datasets into configurable processing chunks."""

    def __init__(self, batch_size: int = 50) -> None:
        """Initialize BatchProcessor.

        Args:
            batch_size: Number of messages per batch (default 50).
        """
        self.batch_size: int = max(1, batch_size)

    def create_batches(
        self,
        df: pd.DataFrame,
    ) -> Generator[pd.DataFrame, None, None]:
        """Yield DataFrames of size batch_size.

        Args:
            df: Input pandas DataFrame.

        Yields:
            Chunked DataFrames.
        """
        total_rows = len(df)
        for i in range(0, total_rows, self.batch_size):
            yield df.iloc[i : i + self.batch_size]
