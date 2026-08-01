"""Confidence Score Calibrator."""

from src.features.feature_vector import FeatureVector
from src.retrieval.retrieval_result import RetrievalResult

CATEGORY_PRIORS: dict[str, float] = {
    "scam": 0.86,
    "spam": 0.80,
    "urgent": 0.78,
    "payment": 0.76,
    "personal": 0.70,
    "event": 0.65,
    "business_update": 0.58,
    "forward": 0.55,
    "promotion": 0.52,
    "greeting": 0.50,
    "unknown": 0.45,
}


class ConfidenceCalibrator:
    """Calibrates confidence scores as a continuous weighted sum over evidence, trust, history, and message signals."""

    def calibrate(
        self,
        base_score: float,
        vector: FeatureVector,
        retrieval_result: RetrievalResult | None,
        action: str,
        message_type: str = "unknown",
    ) -> float:
        """Calibrate confidence score as a continuous signal function.

        Formula:
            Confidence = clip(
                Prior(category)
                + 0.02 * min(evidence_match_count, 3)
                + 0.03 * min(1.0, retrieval_similarity_score)
                + 0.04 * (1 if verified else 0)
                + 0.02 * (1 if trusted_sender else 0)
                + 0.03 * min(1.0, interaction_frequency)
                - 0.04 * (1 if evidence_match_count == 0 else 0)
                + 0.0002 * min(100, len(text)),
                0.38, 0.99
            )

        Returns:
            Calibrated confidence float rounded to 4 decimal places.
        """
        # 1. Starting Category Prior
        prior = CATEGORY_PRIORS.get(message_type, 0.50)

        # 2. Evidence Strength Adjustment
        ev_count = len(retrieval_result.evidence_message_ids) if retrieval_result and retrieval_result.evidence_message_ids else 0
        ret_score = retrieval_result.retrieval_score if retrieval_result else 0.0

        ev_adj = 0.02 * min(ev_count, 3) + 0.03 * min(1.0, ret_score)
        if ev_count == 0:
            ev_adj -= 0.04

        # 3. Trust & Verification Signals
        trust_adj = 0.0
        if getattr(vector, "verified", False) or getattr(vector, "trusted_business", False):
            trust_adj += 0.04
        if getattr(vector, "trusted_sender", False):
            trust_adj += 0.02
        if getattr(vector, "new_sender", False):
            trust_adj -= 0.02

        # 4. Interaction History Signals
        history_adj = 0.0
        freq = getattr(vector, "interaction_frequency", 0.0)
        replies = getattr(vector, "reply_history", 0)
        if freq > 0.0:
            history_adj += min(0.04, freq * 0.05)
        if replies > 0:
            history_adj += min(0.03, replies * 0.01)

        # 5. Message Content Length & Risk Signals
        text_str = getattr(vector, "message_text", "") or ""
        text_adj = min(0.025, len(text_str) * 0.0003)

        risk_adj = 0.0
        if getattr(vector, "contains_scam_keyword", False):
            risk_adj += 0.04
        if getattr(vector, "is_forwarded", False):
            fwd = getattr(vector, "forwarded_count", 1)
            risk_adj += min(0.03, max(0, fwd - 1) * 0.01)

        # 6. Routing Action Adjustment
        action_adj = 0.0
        if action == "digest":
            action_adj -= 0.03
        elif action == "mute" and message_type in ("scam", "spam"):
            action_adj += 0.03

        raw_conf = prior + ev_adj + trust_adj + history_adj + text_adj + risk_adj + action_adj
        return round(min(0.99, max(0.38, raw_conf)), 4)
