"""Unit tests for RankingEngine."""

from config.settings import DATASET_PATH
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.retrieval.ranking import RankingEngine


def test_ranking_engine() -> None:
    """Test ranking engine multi-strategy fusion and Top-K selection."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()
    ctx = ContextManager(repo)
    ctx.build()
    feature_pipe = FeaturePipeline(ctx)

    msg = {"message_id": "MSG_001", "sender_id": "USR_101", "recipient_id": "USR_102", "text_content": "Coffee meeting"}
    vec = feature_pipe.process(msg)

    candidates = list(ctx.history_builder._cache.values())
    strategy_scores = {
        "SenderStrategy": {cand.message_id: 1.0 if cand.sender == "USR_101" else 0.0 for cand in candidates},
        "KeywordStrategy": {cand.message_id: 0.5 for cand in candidates},
    }

    ranker = RankingEngine()
    top_ids, top_score, main_strat, details = ranker.rank(vec, candidates, strategy_scores, ctx, top_k=3)

    assert isinstance(top_ids, list)
    assert len(top_ids) <= 3
    assert 0.0 <= top_score <= 1.0
    assert isinstance(main_strat, str)
