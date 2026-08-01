"""Same Sender Retrieval Strategy."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class SenderStrategy(BaseRetrievalStrategy):
    """Retrieves historical messages involving the same sender or contact."""

    def __init__(self) -> None:
        super().__init__(name="SenderStrategy")

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        target_sender = vector.sender_id

        for cand in candidates:
            if cand.sender == target_sender or cand.user_id == target_sender:
                scores[cand.message_id] = 1.0
            else:
                scores[cand.message_id] = 0.0

        return scores
