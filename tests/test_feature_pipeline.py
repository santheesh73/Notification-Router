"""Unit tests for FeaturePipeline."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.features.feature_vector import FeatureVector
from src.loaders.load_data import DataRepository


def test_feature_pipeline_process() -> None:
    """Test processing single message into FeatureVector."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    pipeline = FeaturePipeline(ctx)
    sample_msg = {
        "message_id": "MSG_TEST_01",
        "sender_id": "BUS_301",
        "recipient_id": "USR_101",
        "timestamp": "2026-08-01 10:20:00",
        "message_type": "text",
        "text_content": "Your order payment of $49.99 has been received.",
    }

    vec = pipeline.process(sample_msg)
    assert isinstance(vec, FeatureVector)
    assert vec.message_id == "MSG_TEST_01"
    assert vec.contains_payment is True
    assert vec.business is True
    assert vec.trusted_business is True


def test_feature_pipeline_dataset() -> None:
    """Test processing full dataset into list of FeatureVectors and generating summary."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    pipeline = FeaturePipeline(ctx)
    msgs_df = repo.get_dataframe("messages")
    vectors = pipeline.process_dataset(msgs_df)

    assert len(vectors) == len(msgs_df)
    summary_str = pipeline.summary(vectors)
    assert "Total Feature Vectors" in summary_str
    assert "Average Message Length" in summary_str
