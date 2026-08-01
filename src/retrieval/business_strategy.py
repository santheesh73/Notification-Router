"""Same Business Retrieval Strategy."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class BusinessStrategy(BaseRetrievalStrategy):
    """Retrieves historical messages involving the same business account."""

    def __init__(self) -> None:
        super().__init__(name="BusinessStrategy")

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        target_biz = vector.business_id

        if not target_biz:
            return {cand.message_id: 0.0 for cand in candidates}

        for cand in candidates:
            if cand.sender == target_biz or target_biz in cand.conversation:
                scores[cand.message_id] = 1.0
            else:
                scores[cand.message_id] = 0.0

        return scores
