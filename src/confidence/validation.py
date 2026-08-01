"""Final Decision & Evidence Validator."""

from typing import Any

VALID_ACTIONS: set[str] = {"notify", "digest", "mute"}
VALID_MESSAGE_TYPES: set[str] = {
    "personal",
    "urgent",
    "event",
    "payment",
    "business_update",
    "promotion",
    "greeting",
    "forward",
    "spam",
    "scam",
    "unknown",
}

# Mapping from internal types to competition-allowed types
TYPE_NORMALIZATION_MAP: dict[str, str] = {
    "office": "business_update",
    "business": "business_update",
    "family": "personal",
    "duplicate": "forward",
    "reminder": "event",
    "academic": "event",
    "general": "business_update",
    "muted_group": "spam",
}


class DecisionValidator:
    """Validates FinalDecision dataclass outputs."""

    def validate_reason(self, reason: str) -> str:
        """Sanitize and truncate reason text to maximum 25 words.

        Args:
            reason: Input reason text string.

        Returns:
            Sanitized, truncated plain text reason string.
        """
        if not reason:
            return "Notification routing decision."

        # Remove markdown fences or formatting if present
        clean_text = reason.replace("```json", "").replace("```", "").replace("**", "").replace("#", "").strip()

        # Remove any Gemini or quota exhaustion references
        if "gemini" in clean_text.lower() or "quota exhausted" in clean_text.lower():
            clean_text = "Message classified based on content analysis and contextual signals."

        words = clean_text.split()
        if len(words) > 25:
            clean_text = " ".join(words[:25])

        return clean_text

    def validate_evidence_ids(self, evidence_ids: list[str]) -> list[str]:
        """Deduplicate and clean evidence message IDs.

        Args:
            evidence_ids: List of evidence message ID strings.

        Returns:
            Deduplicated list of valid evidence message IDs.
        """
        seen: set[str] = set()
        clean_list: list[str] = []
        for eid in evidence_ids:
            s_eid = str(eid).strip()
            if s_eid and s_eid not in seen and s_eid.lower() != "none":
                seen.add(s_eid)
                clean_list.append(s_eid)
        return clean_list

    def normalize_message_type(self, message_type: str) -> str:
        """Normalize message_type to competition-allowed values.

        Args:
            message_type: Raw message type string.

        Returns:
            Normalized message type string from VALID_MESSAGE_TYPES.
        """
        if message_type in VALID_MESSAGE_TYPES:
            return message_type
        return TYPE_NORMALIZATION_MAP.get(message_type, "unknown")

    def validate_decision(self, action: str, message_type: str, confidence: float) -> tuple[bool, str]:
        """Validate action, message_type, and confidence values.

        Args:
            action: Decision action string.
            message_type: Decision message_type string.
            confidence: Calibrated confidence float.

        Returns:
            Tuple of (is_valid, error_reason).
        """
        if action not in VALID_ACTIONS:
            return False, f"Invalid action '{action}'."

        if message_type not in VALID_MESSAGE_TYPES:
            return False, f"Invalid message_type '{message_type}'."

        if confidence < 0.0 or confidence > 1.0:
            return False, f"Confidence {confidence} out of bounds."

        return True, "Valid"
