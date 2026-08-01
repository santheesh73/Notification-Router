"""User Interaction Retrieval Strategy."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class InteractionStrategy(BaseRetrievalStrategy):
    """Scores candidates based on historical user interaction signals (replied, opened, reported)."""

    def __init__(self) -> None:
        super().__init__(name="InteractionStrategy")

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        for cand in candidates:
            if cand.replied:
                score = 1.0
            elif cand.opened:
                score = 0.8
            elif cand.dismissed:
                score = 0.4
            elif cand.reported:
                score = 0.1
            else:
                score = 0.5

            scores[cand.message_id] = score

        return scores
