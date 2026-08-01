"""Multi-Strategy Score Fusion & Ranking Engine."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.models.history_profile import HistoryProfile
from src.retrieval.retrieval_strategy import BaseRetrievalStrategy


class RankingEngine:
    """Combines candidate scores across multiple retrieval strategies and selects Top-K evidence."""

    def __init__(self, strategy_weights: dict[str, float] | None = None) -> None:
        """Initialize RankingEngine with optional strategy weights.

        Args:
            strategy_weights: Dictionary mapping strategy name to float weight.
        """
        self.weights: dict[str, float] = strategy_weights or {
            "SenderStrategy": 0.25,
            "BusinessStrategy": 0.25,
            "GroupStrategy": 0.25,
            "KeywordStrategy": 0.15,
            "InteractionStrategy": 0.05,
            "RecencyStrategy": 0.05,
        }

    def rank(
        self,
        vector: FeatureVector,
        candidates: list[HistoryProfile],
        strategy_scores: dict[str, dict[str, float]],
        context: ContextManager,
        top_k: int = 5,
    ) -> tuple[list[str], float, str, dict[str, Any]]:
        """Combine strategy scores, rank candidates, and select Top-K evidence message IDs.

        Args:
            vector: Current FeatureVector.
            candidates: List of candidate HistoryProfiles.
            strategy_scores: Dict mapping strategy_name -> {message_id: score}.
            context: ContextManager instance.
            top_k: Number of evidence message IDs to return (default 5).

        Returns:
            Tuple of (top_k_evidence_ids, overall_retrieval_score, primary_matched_strategy, similarity_details).
        """
        if not candidates or not strategy_scores:
            return [], 0.0, "none", {}

        # 1. Calculate Combined Score per Candidate
        combined_scores: dict[str, float] = {}
        total_weight = sum(self.weights.get(s_name, 0.1) for s_name in strategy_scores.keys())

        for cand in candidates:
            cand_id = cand.message_id
            weighted_sum = 0.0
            for strat_name, scores_map in strategy_scores.items():
                w = self.weights.get(strat_name, 0.1)
                weighted_sum += scores_map.get(cand_id, 0.0) * w

            norm_score = round(min(1.0, max(0.0, weighted_sum / max(1e-5, total_weight))), 4)
            combined_scores[cand_id] = norm_score

        # 2. Filter out current message itself and sort descending
        filtered_scores = {cid: sc for cid, sc in combined_scores.items() if cid != vector.message_id and sc > 0.0}

        if not filtered_scores:
            return [], 0.0, "none", {}

        sorted_candidates = sorted(filtered_scores.items(), key=lambda item: item[1], reverse=True)
        top_candidates = sorted_candidates[:top_k]
        top_ids = [cid for cid, _ in top_candidates]
        best_score = top_candidates[0][1] if top_candidates else 0.0

        # Determine primary matched strategy based on highest contribution
        primary_strategy = "none"
        max_strat_val = -1.0
        for s_name, s_map in strategy_scores.items():
            if top_ids and s_map.get(top_ids[0], 0.0) > max_strat_val:
                max_strat_val = s_map.get(top_ids[0], 0.0)
                primary_strategy = s_name

        similarity_details = {
            "top_candidate_scores": dict(top_candidates),
            "total_candidates_evaluated": len(candidates),
        }

        return top_ids, best_score, primary_strategy, similarity_details
