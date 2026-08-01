"""JSON Response Extractor and Parser for LLM Responses."""

import json
import re
from typing import Any

from src.utils.logger import logger


class ResponseParser:
    """Robust JSON response extractor and schema validator for LLM outputs."""

    VALID_ACTIONS = {"notify", "digest", "mute"}
    VALID_MESSAGE_TYPES = {
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
        "academic",
        "general",
        "business",
    }

    def parse(self, text: str) -> dict[str, Any]:
        """Instance method wrapper for parse_json.

        Args:
            text: Raw output string from LLM provider.

        Returns:
            Parsed dictionary matching required schema.
        """
        return self.parse_json(text)

    @classmethod
    def parse_json(cls, text: str) -> dict[str, Any]:
        """Extract and parse clean JSON payload from raw LLM output text.

        Args:
            text: Raw output string from LLM provider.

        Returns:
            Parsed dictionary matching required schema.

        Raises:
            ValueError: If valid JSON cannot be extracted or required fields are missing.
        """
        if not text or not text.strip():
            raise ValueError("Empty response text from LLM provider.")

        clean_text = text.strip()

        # 1. Strip markdown code fence block wrappers (```json ... ``` or ``` ... ```)
        if "```" in clean_text:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
            if match:
                clean_text = match.group(1)
            else:
                # Remove fence markers manually
                clean_text = re.sub(r"^```(?:json)?", "", clean_text, flags=re.IGNORECASE)
                clean_text = re.sub(r"```$", "", clean_text)
                clean_text = clean_text.strip()

        # 2. Extract first matching JSON object `{ ... }`
        if not (clean_text.startswith("{") and clean_text.endswith("}")):
            json_match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group(1)

        # 3. Parse JSON string
        try:
            data = json.loads(clean_text)
        except json.JSONDecodeError as exc:
            logger.warning(f"ResponseParser JSON decode error: {exc} on text: {clean_text[:100]}")
            raise ValueError(f"Failed to decode JSON from response: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("Parsed JSON payload is not a dictionary.")

        # 4. Validate and Sanitize Fields
        action = str(data.get("action", "digest")).lower()
        if action not in cls.VALID_ACTIONS:
            action = "digest"

        m_type = str(data.get("message_type", "unknown")).lower()

        reason = str(data.get("reason", "AI LLM decision."))
        if len(reason) > 200:
            reason = reason[:197] + "..."

        try:
            conf = float(data.get("confidence", 0.85))
            conf = max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            conf = 0.85

        return {
            "action": action,
            "message_type": m_type,
            "reason": reason,
            "confidence": conf,
        }
