"""Unit tests for RetrievalEngine and RetrievalPipeline."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.retrieval.retrieval_engine import RetrievalEngine
from src.retrieval.retrieval_pipeline import RetrievalPipeline, RetrievalValidationReport
from src.retrieval.retrieval_result import RetrievalResult


def test_retrieval_engine() -> None:
    """Test RetrievalEngine retrieve single message."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    msg = {"message_id": "MSG_001", "sender_id": "USR_101", "recipient_id": "USR_102", "text_content": "Coffee meeting"}
    vec = feature_pipe.process(msg)

    engine = RetrievalEngine()
    result = engine.retrieve(vec, ctx, top_k=5)

    assert isinstance(result, RetrievalResult)
    assert result.message_id == "MSG_001"
    assert isinstance(result.evidence_message_ids, list)


def test_retrieval_pipeline_batch() -> None:
    """Test batch processing and summary generation."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()

    feature_pipe = FeaturePipeline(ctx)
    msgs_df = repo.get_dataframe("messages")
    vectors = feature_pipe.process_dataset(msgs_df)

    pipeline = RetrievalPipeline()
    results = pipeline.process_batch(vectors, ctx, top_k=5)

    assert len(results) == len(vectors)

    report = pipeline.validate(results)
    assert isinstance(report, RetrievalValidationReport)
    assert report.is_valid is True

    summary_str = pipeline.summary(results)
    assert "Total Messages Evaluated" in summary_str
    assert "Average Evidence Items Per Message" in summary_str
