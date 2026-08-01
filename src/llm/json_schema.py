"""JSON Schema for LLM Response Validation."""

from typing import Any

LLM_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["action", "message_type", "reason", "confidence"],
    "properties": {
        "action": {
            "type": "string",
            "enum": ["notify", "digest", "mute"],
        },
        "message_type": {
            "type": "string",
            "enum": [
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
            ],
        },
        "reason": {
            "type": "string",
            "maxLength": 200,
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
    },
    "additionalProperties": False,
}
