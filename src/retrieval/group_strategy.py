"""Same Group Retrieval Strategy."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class GroupStrategy(BaseRetrievalStrategy):
    """Retrieves historical messages from the same group chat."""

    def __init__(self) -> None:
        super().__init__(name="GroupStrategy")

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        target_group = vector.group_id

        if not target_group:
            return {cand.message_id: 0.0 for cand in candidates}

        for cand in candidates:
            if target_group in cand.conversation or cand.sender == target_group:
                scores[cand.message_id] = 1.0
            else:
                scores[cand.message_id] = 0.0

        return scores
