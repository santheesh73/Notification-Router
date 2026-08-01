"""Unit tests for FeatureVector validation."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline, FeatureValidationReport
from src.loaders.load_data import DataRepository


def test_feature_validation_report() -> None:
    """Test validation report generation for feature vectors."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    pipeline = FeaturePipeline(ctx)
    msgs_df = repo.get_dataframe("messages")
    vectors = pipeline.process_dataset(msgs_df)

    report = pipeline.validate(vectors)
    assert isinstance(report, FeatureValidationReport)
    assert report.is_valid is True
