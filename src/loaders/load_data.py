"""Data Repository and CSV Loader module.

Provides DataRepository class for loading, validating, and summarizing all 13 CSV datasets
for the AI-powered WhatsApp Message Notification Router system.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate

from config.settings import DATASET_PATH
from src.utils.logger import logger

# List of all 13 required CSV dataset names (without extension)
REQUIRED_DATASETS: list[str] = [
    "messages",
    "sample_messages",
    "users",
    "groups",
    "group_members",
    "business_accounts",
    "user_business_history",
    "message_history",
    "message_events",
    "images",
    "voice_notes",
    "daily_notification_summary",
    "output",
]


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================


class DataRepositoryError(Exception):
    """Base exception for all DataRepository errors."""

    pass


class MissingFolderError(DataRepositoryError):
    """Raised when the specified dataset directory does not exist."""

    pass


class DatasetNotFoundError(DataRepositoryError):
    """Raised when a requested dataset CSV file is missing."""

    pass


class CorruptedCSVError(DataRepositoryError):
    """Raised when a CSV file cannot be parsed due to syntax/format corruption."""

    pass


class EmptyCSVError(DataRepositoryError):
    """Raised when a CSV file exists but contains no data (0 bytes or 0 rows)."""

    pass


class InvalidEncodingError(DataRepositoryError):
    """Raised when a CSV file cannot be read due to character encoding issues."""

    pass


class MissingColumnError(DataRepositoryError):
    """Raised when required schema columns are absent from a dataset."""

    pass


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class ValidationReport:
    """Structured validation result for a single dataset DataFrame."""

    dataset_name: str
    rows: int
    columns: int
    column_names: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    duplicate_rows: int
    memory_usage_bytes: int
    memory_usage_formatted: str

    def to_dict(self) -> dict[str, Any]:
        """Convert validation report to dictionary format."""
        return asdict(self)


# =============================================================================
# DataRepository Implementation
# =============================================================================


class DataRepository:
    """Repository class managing the ingestion, validation, and summary of datasets."""

    def __init__(self, dataset_path: Path | None = None, input_file: Path | None = None) -> None:
        """Initialize DataRepository.

        Args:
            dataset_path: Path to dataset directory. Defaults to DATASET_PATH setting.
            input_file: Path to input messages CSV file. Defaults to dataset_path/messages.csv.
        """
        self.dataset_path: Path = dataset_path or DATASET_PATH
        self.input_file: Path | None = input_file
        self._data_frames: dict[str, pd.DataFrame] = {}
        self._validation_reports: dict[str, ValidationReport] = {}

    @property
    def datasets(self) -> dict[str, pd.DataFrame]:
        """Expose loaded dataframes dictionary."""
        return self._data_frames

    def _format_memory(self, bytes_val: int) -> str:
        """Format byte size into human-readable string (KB, MB).

        Args:
            bytes_val: Memory usage in bytes.

        Returns:
            Human-readable string formatted to 1 decimal place.
        """
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        else:
            return f"{bytes_val / (1024 * 1024):.1f} MB"

    def load_single_csv(self, file_path: Path) -> pd.DataFrame:
        """Load a single CSV file with error handling.

        Args:
            file_path: Path to CSV file.

        Returns:
            Loaded pandas DataFrame.

        Raises:
            DatasetNotFoundError: If file does not exist.
            EmptyCSVError: If file is empty.
            InvalidEncodingError: If file encoding is invalid.
            CorruptedCSVError: If file content is unparseable.
        """
        if not file_path.exists():
            raise DatasetNotFoundError(f"Dataset file missing: {file_path}")

        if file_path.stat().st_size == 0:
            raise EmptyCSVError(f"Dataset file is empty (0 bytes): {file_path}")

        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError as exc:
            logger.error(f"Encoding error reading {file_path}: {exc}")
            raise InvalidEncodingError(f"Invalid UTF-8 encoding in {file_path}") from exc
        except pd.errors.EmptyDataError as exc:
            logger.error(f"Empty data error reading {file_path}: {exc}")
            raise EmptyCSVError(f"No columns or data to parse in {file_path}") from exc
        except pd.errors.ParserError as exc:
            logger.error(f"Parser error reading {file_path}: {exc}")
            raise CorruptedCSVError(f"Corrupted CSV structure in {file_path}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error loading {file_path}: {exc}")
            raise DataRepositoryError(f"Failed to load dataset {file_path}: {exc}") from exc

        if df.empty and len(df.columns) == 0:
            raise EmptyCSVError(f"DataFrame loaded from {file_path} is empty with 0 columns.")

        return df

    def load_all(self, input_file: Path | None = None) -> dict[str, pd.DataFrame]:
        """Load all required CSV datasets from dataset_path.

        Args:
            input_file: Optional input CSV path for messages. Defaults to self.input_file or dataset_path/messages.csv.

        Returns:
            Dictionary mapping dataset names to DataFrames.

        Raises:
            MissingFolderError: If dataset directory is missing.
        """
        if not self.dataset_path.exists() or not self.dataset_path.is_dir():
            msg = f"Dataset folder does not exist at: {self.dataset_path}"
            logger.error(msg)
            raise MissingFolderError(msg)

        logger.info(f"Loading datasets from: {self.dataset_path}")
        target_input = input_file or self.input_file

        for name in REQUIRED_DATASETS:
            if name == "messages" and target_input and target_input.exists():
                csv_path = target_input
            else:
                csv_path = self.dataset_path / f"{name}.csv"

            try:
                df = self.load_single_csv(csv_path)
                self._data_frames[name] = df
                logger.success(f"Successfully loaded '{name}' ({len(df)} rows, {len(df.columns)} columns)")
            except DataRepositoryError as err:
                logger.warning(f"Could not load dataset '{name}': {err}")
                raise

        return self._data_frames

    def get_dataframe(self, name: str) -> pd.DataFrame:
        """Retrieve a loaded DataFrame by dataset name.

        Args:
            name: Name of dataset (without .csv extension).

        Returns:
            pandas DataFrame.

        Raises:
            DatasetNotFoundError: If dataset is not loaded.
        """
        if name not in self._data_frames:
            msg = f"Dataset '{name}' has not been loaded into memory."
            logger.error(msg)
            raise DatasetNotFoundError(msg)
        return self._data_frames[name]

    def list_datasets(self) -> list[str]:
        """Return list of currently loaded dataset names.

        Returns:
            List of loaded dataset keys.
        """
        return list(self._data_frames.keys())

    def get_schema(self, name: str) -> dict[str, str]:
        """Get column names and data types for a given dataset.

        Args:
            name: Name of dataset.

        Returns:
            Dictionary mapping column name to data type string.
        """
        df = self.get_dataframe(name)
        return {col: str(dtype) for col, dtype in df.dtypes.items()}

    def validate(self) -> dict[str, ValidationReport]:
        """Validate every loaded CSV dataset and compute statistics.

        Returns:
            Dictionary mapping dataset name to ValidationReport object.
        """
        self._validation_reports.clear()

        for name, df in self._data_frames.items():
            mem_bytes = int(df.memory_usage(deep=True).sum())
            missing_dict = {col: int(val) for col, val in df.isnull().sum().items()}
            report = ValidationReport(
                dataset_name=name,
                rows=len(df),
                columns=len(df.columns),
                column_names=list(df.columns),
                dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
                missing_values=missing_dict,
                duplicate_rows=int(df.duplicated().sum()),
                memory_usage_bytes=mem_bytes,
                memory_usage_formatted=self._format_memory(mem_bytes),
            )
            self._validation_reports[name] = report
            logger.debug(f"Validated dataset '{name}': {len(df)} rows, {report.duplicate_rows} duplicates.")

        return self._validation_reports

    def summary(self) -> str:
        """Generate and print a formatted ASCII table of all datasets.

        Returns:
            Formatted string table of dataset metrics.
        """
        if not self._validation_reports:
            self.validate()

        table_data = []
        for name in REQUIRED_DATASETS:
            if name in self._data_frames:
                rep = self._validation_reports[name]
                table_data.append([
                    rep.dataset_name,
                    rep.rows,
                    rep.columns,
                    rep.memory_usage_formatted,
                    "Yes",
                ])
            else:
                table_data.append([name, 0, 0, "0 B", "No"])

        headers = ["Dataset", "Rows", "Columns", "Memory", "Loaded"]
        formatted_table = tabulate(table_data, headers=headers, tablefmt="grid")
        return formatted_table
