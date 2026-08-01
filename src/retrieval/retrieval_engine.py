"""Historical Evidence Retrieval Engine."""

import re
from typing import Any

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.cache import RetrievalCache
from src.retrieval.retrieval_result import RetrievalResult
from src.utils.logger import logger

STOP_WORDS: set[str] = {
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "is", "are", "am", "be",
    "this", "that", "it", "you", "i", "we", "my", "your", "and", "or", "but", "dear", "customer", "please"
}


class RetrievalEngine:
    """Deterministic Historical Evidence Retrieval Engine for identifying Top-3 supporting evidence."""

    def __init__(
        self,
        cache: RetrievalCache | None = None,
    ) -> None:
        """Initialize RetrievalEngine.

        Args:
            cache: Optional custom RetrievalCache instance.
        """
        self.cache: RetrievalCache = cache or RetrievalCache()

    def _extract_tokens(self, text: str) -> set[str]:
        """Extract significant lowercase tokens from text string."""
        if not text or text == "nan":
            return set()
        words = re.findall(r"\w+", str(text).lower())
        return {w for w in words if w not in STOP_WORDS and len(w) > 2}

    def retrieve(
        self,
        vector: FeatureVector,
        context: ContextManager,
        top_k: int = 3,
    ) -> RetrievalResult:
        """Retrieve Top-3 historical evidence messages supporting the routing decision.

        Searches message_history using sender, business, group, keyword overlap, media type, and text similarity.

        Args:
            vector: Extracted FeatureVector instance.
            context: ContextManager instance.
            top_k: Number of evidence message IDs to return (default 3).

        Returns:
            RetrievalResult instance.
        """
        # 1. Check Cache
        cached_res = self.cache.get(vector.message_id)
        if cached_res:
            return cached_res

        all_hist = list(context.history_builder._cache.values())
        if not all_hist:
            res = RetrievalResult(
                message_id=vector.message_id,
                retrieved=False,
                evidence_message_ids=[],
                retrieval_score=0.0,
                matched_strategy="none",
            )
            self.cache.set(vector.message_id, res)
            return res

        # Extract current message attributes
        target_sender = str(vector.sender_id) if vector.sender_id else ""
        target_biz = str(vector.business_id) if vector.business_id else ""
        target_grp = str(vector.group_id) if vector.group_id else ""
        target_media = str(vector.media_type) if vector.media_type else ""
        target_user = str(vector.user_id) if vector.user_id else ""
        target_text = getattr(vector, "message_text", "") or ""
        target_tokens = self._extract_tokens(target_text)

        candidates_scores: list[tuple[str, float]] = []

        for hp in all_hist:
            # Exclude current message itself
            if hp.message_id == vector.message_id:
                continue

            score = 0.0

            # 1. Sender match
            if target_sender and target_sender != "unknown" and (hp.sender == target_sender or hp.user_id == target_sender):
                score += 0.45

            # 2. Business match
            if target_biz and (hp.business_id == target_biz or hp.sender == target_biz):
                score += 0.45

            # 3. Group match
            if target_grp and hp.group_id == target_grp:
                score += 0.40

            # 4. Same recipient user
            if target_user and hp.user_id == target_user:
                score += 0.15

            # 5. Media type match
            if target_media and target_media != "text" and hp.media_type == target_media:
                score += 0.20

            # 6. Keyword and Text Similarity Overlap
            if target_tokens and hp.message_text:
                cand_tokens = self._extract_tokens(hp.message_text)
                if cand_tokens:
                    inter = target_tokens.intersection(cand_tokens)
                    if inter:
                        union = target_tokens.union(cand_tokens)
                        jaccard = len(inter) / max(1, len(union))
                        score += jaccard * 0.60

            # Collect candidate if score crosses relevance threshold
            if score >= 0.10:
                candidates_scores.append((hp.message_id, round(score, 4)))

        # Sort candidates descending by score
        candidates_scores.sort(key=lambda item: item[1], reverse=True)

        top_evidence_ids = [cid for cid, _ in candidates_scores[:top_k]]
        best_score = candidates_scores[0][1] if candidates_scores else 0.0

        retrieved_flag = len(top_evidence_ids) > 0 and best_score > 0.0

        res = RetrievalResult(
            message_id=vector.message_id,
            retrieved=retrieved_flag,
            evidence_message_ids=top_evidence_ids,
            retrieval_score=best_score,
            matched_strategy="MultiSignalHistorySearch" if retrieved_flag else "none",
        )

        self.cache.set(vector.message_id, res)
        logger.debug(f"Retrieved {len(top_evidence_ids)} evidence items for '{vector.message_id}' (Score={best_score:.4f}).")
        return res
