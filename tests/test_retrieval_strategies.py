"""Unit tests for individual retrieval strategies and namespace integrity."""

import pandas as pd

from config.settings import DATASET_PATH, OUTPUT_CSV_PATH
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


def test_evidence_namespace_isolation() -> None:
    """SECTION 1 Unit Test: Assert all evidence IDs are members of message_history.csv and ZERO are from messages.csv."""
    repo = DataRepository(dataset_path=DATASET_PATH)
    repo.load_all()

    m_df = repo.get_dataframe("messages")
    h_df = repo.get_dataframe("message_history")

    current_batch_ids = set(m_df["message_id"].astype(str)) if not m_df.empty else set()
    history_ids = set(h_df["message_id"].astype(str)) if not h_df.empty else set()

    if not OUTPUT_CSV_PATH.exists():
        return

    out_df = pd.read_csv(OUTPUT_CSV_PATH)
    invalid_citations = []

    for idx, row in out_df.iterrows():
        msg_id = str(row["message_id"])
        ev_str = str(row["evidence_message_ids"])

        if ev_str and ev_str != "none" and pd.notnull(ev_str):
            parts = [p.strip() for p in ev_str.split(";")]
            for eid in parts:
                # 1. Must NOT be from current batch (messages.csv)
                if eid in current_batch_ids or eid.startswith("msg_"):
                    invalid_citations.append(f"Row {msg_id}: Evidence '{eid}' comes from current batch (messages.csv)!")

                # 2. Must belong to message_history.csv
                if history_ids and eid not in history_ids:
                    invalid_citations.append(f"Row {msg_id}: Evidence '{eid}' not found in message_history.csv!")

    assert len(invalid_citations) == 0, f"Evidence namespace isolation violated:\n" + "\n".join(invalid_citations)
