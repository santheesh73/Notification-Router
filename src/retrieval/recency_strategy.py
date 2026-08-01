"""Recency & Time Decay Retrieval Strategy."""

from datetime import datetime
import pandas as pd

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class RecencyStrategy(BaseRetrievalStrategy):
    """Scores candidate historical messages based on recency with exponential time decay."""

    def __init__(self) -> None:
        super().__init__(name="RecencyStrategy")

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        cur_ts = vector.timestamp
        dt_cur = pd.to_datetime(cur_ts).to_pydatetime() if cur_ts else datetime.now()

        for cand in candidates:
            if not cand.event_time:
                scores[cand.message_id] = 0.5
                continue

            try:
                dt_cand = pd.to_datetime(cand.event_time).to_pydatetime()
                diff_hours = abs((dt_cur - dt_cand).total_seconds()) / 3600.0
                # Decay factor: max 1.0, minus 0.02 per hour difference
                score = round(max(0.1, min(1.0, 1.0 - (diff_hours * 0.02))), 4)
            except Exception:
                score = 0.5

            scores[cand.message_id] = score

        return scores
