"""LLM Response Validator."""

from typing import Any

VALID_ACTIONS: set[str] = {"notify", "digest", "mute"}
VALID_MESSAGE_TYPES: set[str] = {
    "personal",
    "urgent",
    "event",
    "payment",
    "business",
    "business_update",
    "promotion",
    "greeting",
    "forward",
    "spam",
    "scam",
    "muted_group",
    "duplicate",
    "unknown",
}


class ResponseValidator:
    """Validates parsed LLM JSON dictionary against strict schema rules."""

    def validate(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Validate response dictionary.

        Args:
            data: Parsed dictionary from ResponseParser.

        Returns:
            Tuple of (is_valid, error_reason).
        """
        if not data or not isinstance(data, dict):
            return False, "Output is not a valid dictionary."

        # Required keys check
        required = ["action", "message_type", "reason", "confidence"]
        for key in required:
            if key not in data:
                return False, f"Missing required key '{key}'."

        action = str(data["action"]).lower()
        if action not in VALID_ACTIONS:
            return False, f"Invalid action '{action}'. Allowed: {VALID_ACTIONS}"

        msg_type = str(data["message_type"]).lower()
        if msg_type not in VALID_MESSAGE_TYPES:
            return False, f"Invalid message_type '{msg_type}'. Allowed: {VALID_MESSAGE_TYPES}"

        try:
            conf = float(data["confidence"])
            if conf < 0.0 or conf > 1.0:
                return False, f"Confidence {conf} out of bounds [0.0, 1.0]."
        except (ValueError, TypeError):
            return False, "Confidence is not a valid float."

        reason = str(data["reason"]).strip()
        if not reason:
            return False, "Reason string is empty."

        return True, "Valid"
