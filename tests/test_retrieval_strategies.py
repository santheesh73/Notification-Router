"""Unit tests for individual retrieval strategies."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.retrieval.business_strategy import BusinessStrategy
from src.retrieval.group_strategy import GroupStrategy
from src.retrieval.keyword_strategy import KeywordStrategy
from src.retrieval.sender_strategy import SenderStrategy


def test_sender_strategy() -> None:
    """Test SenderStrategy scoring."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M1", "sender_id": "USR_101", "recipient_id": "USR_102", "text_content": "Hello"}
    vec = feature_pipe.process(msg)

    candidates = list(ctx.history_builder._cache.values())
    strat = SenderStrategy()
    scores = strat.score_candidates(vec, candidates, ctx)

    assert isinstance(scores, dict)
    assert len(scores) == len(candidates)


def test_business_strategy() -> None:
    """Test BusinessStrategy scoring."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_BUS", "sender_id": "BUS_301", "recipient_id": "USR_101", "text_content": "Order shipped"}
    vec = feature_pipe.process(msg)

    candidates = list(ctx.history_builder._cache.values())
    strat = BusinessStrategy()
    scores = strat.score_candidates(vec, candidates, ctx)

    assert isinstance(scores, dict)


def test_group_strategy() -> None:
    """Test GroupStrategy scoring."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "M_GRP", "sender_id": "USR_103", "group_id": "GRP_501", "text_content": "DevOps update"}
    vec = feature_pipe.process(msg)

    candidates = list(ctx.history_builder._cache.values())
    strat = GroupStrategy()
    scores = strat.score_candidates(vec, candidates, ctx)

    assert isinstance(scores, dict)


def test_keyword_strategy() -> None:
    """Test KeywordStrategy scoring."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "MSG_001", "sender_id": "USR_101", "text_content": "Hey are we meeting for coffee today?"}
    vec = feature_pipe.process(msg)

    candidates = list(ctx.history_builder._cache.values())
    strat = KeywordStrategy()
    scores = strat.score_candidates(vec, candidates, ctx)

    assert isinstance(scores, dict)
