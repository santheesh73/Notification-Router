"""Keyword & Token Overlap Retrieval Strategy."""

import re

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy

STOP_WORDS: set[str] = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "is", "are", "am", "be", "this", "that", "it", "you", "i", "we", "my", "your", "and", "or", "but"
}


class KeywordStrategy(BaseRetrievalStrategy):
    """Retrieves historical messages based on keyword and token overlap."""

    def __init__(self) -> None:
        super().__init__(name="KeywordStrategy")

    def _extract_tokens(self, text: str) -> set[str]:
        words = re.findall(r"\w+", text.lower())
        return {w for w in words if w not in STOP_WORDS and len(w) > 2}

    def score_candidates(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        context: ContextManager,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        # Fetch original text from messages table if available
        msgs_df = context.repository.get_dataframe("messages")
        current_text = ""
        if not msgs_df.empty and "message_id" in msgs_df.columns:
            target_row = msgs_df[msgs_df["message_id"].astype(str) == vector.message_id]
            if not target_row.empty:
                current_text = str(target_row.iloc[0].get("text_content", ""))

        target_tokens = self._extract_tokens(current_text)
        if not target_tokens:
            return {cand.message_id: 0.0 for cand in candidates}

        for cand in candidates:
            cand_tokens = self._extract_tokens(cand.conversation + " " + cand.sender)
            if not cand_tokens:
                scores[cand.message_id] = 0.0
                continue

            intersection = target_tokens.intersection(cand_tokens)
            union = target_tokens.union(cand_tokens)
            jaccard = len(intersection) / max(1, len(union))
            scores[cand.message_id] = round(min(1.0, jaccard * 2.0), 4)

        return scores
