"""Unit tests for MediaManager and MediaPipeline."""

import pandas as pd

from config.settings import DATASET_PATH
from src.loaders.load_data import DataRepository
from src.media.media_manager import MediaManager
from src.media.media_pipeline import MediaPipeline, MediaValidationReport
from src.media.media_result import MediaResult


def test_media_manager_text_message() -> None:
    """Test MediaManager handling non-media text message."""
    manager = MediaManager()
    msg = {"message_id": "MSG_TXT", "message_type": "text", "has_media": False}

    res = manager.process_media(msg)

    assert isinstance(res, MediaResult)
    assert res.media_type == "none"
    assert res.processed is False


def test_media_pipeline_batch() -> None:
    """Test MediaPipeline batch processing on messages dataset."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    msgs_df = repo.get_dataframe("messages")

    pipeline = MediaPipeline()
    results = pipeline.process_batch(msgs_df)

    assert len(results) == len(msgs_df)

    report = pipeline.validate(results)
    assert isinstance(report, MediaValidationReport)
    assert report.is_valid is True

    summary_str = pipeline.summary(results)
    assert "Total Messages Evaluated" in summary_str
    assert "Images Processed" in summary_str
