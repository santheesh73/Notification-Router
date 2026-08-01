"""Unit tests for DataRepository and CSV loaders."""

from pathlib import Path
import tempfile

import pandas as pd
import pytest

from config.settings import DATASET_PATH
from src.loaders.load_data import (
    CorruptedCSVError,
    DataRepository,
    DatasetNotFoundError,
    EmptyCSVError,
    MissingFolderError,
    REQUIRED_DATASETS,
    ValidationReport,
)


def test_data_repository_load_all() -> None:
    """Test loading all 13 CSV datasets from standard dataset path."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    loaded_data = repo.load_all()

    assert len(loaded_data) == 13
    for dataset_name in REQUIRED_DATASETS:
        assert dataset_name in loaded_data
        assert isinstance(loaded_data[dataset_name], pd.DataFrame)
        assert len(loaded_data[dataset_name]) > 0


def test_get_dataframe_and_list() -> None:
    """Test retrieving individual DataFrames and listing dataset names."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    dataset_list = repo.list_datasets()
    assert len(dataset_list) == 13
    assert "messages" in dataset_list

    messages_df = repo.get_dataframe("messages")
    assert isinstance(messages_df, pd.DataFrame)
    assert "message_id" in messages_df.columns

    with pytest.raises(DatasetNotFoundError):
        repo.get_dataframe("non_existent_dataset")


def test_validation_report() -> None:
    """Test validation reports and memory metrics computation."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    reports = repo.validate()
    assert len(reports) == 13
    assert "users" in reports

    users_report = reports["users"]
    assert isinstance(users_report, ValidationReport)
    assert users_report.rows > 0
    assert users_report.columns > 0
    assert "user_id" in users_report.column_names
    assert users_report.memory_usage_bytes > 0
    assert users_report.memory_usage_formatted != ""


def test_summary_generation() -> None:
    """Test ASCII summary table generation."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    summary_str = repo.summary()
    assert isinstance(summary_str, str)
    assert "Dataset" in summary_str
    assert "messages" in summary_str
    assert "users" in summary_str


def test_missing_folder_exception() -> None:
    """Test MissingFolderError when dataset directory does not exist."""
    fake_path = Path("non_existent_directory_xyz_123")
    repo = DataRepository(dataset_path=fake_path)

    with pytest.raises(MissingFolderError):
        repo.load_all()


def test_empty_csv_exception() -> None:
    """Test EmptyCSVError when loading a 0-byte CSV file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        empty_file = tmp_path / "empty.csv"
        empty_file.touch()

        repo = DataRepository(dataset_path=tmp_path)
        with pytest.raises(EmptyCSVError):
            repo.load_single_csv(empty_file)


def test_corrupted_csv_exception() -> None:
    """Test CorruptedCSVError when reading malformed CSV."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        corrupted_file = tmp_path / "corrupted.csv"
        # Write corrupted multi-column mismatch content
        corrupted_file.write_text("a,b,c\n1,2\n3,4,5,6,7,8\n", encoding="utf-8")

        repo = DataRepository(dataset_path=tmp_path)
        with pytest.raises(CorruptedCSVError):
            repo.load_single_csv(corrupted_file)
