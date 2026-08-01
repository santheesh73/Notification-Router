"""Image Vision Output Parser."""

import json
from typing import Any


class ImageParser:
    """Parses raw vision model output into structured dictionary."""

    def parse(self, raw_output: str | dict[str, Any]) -> dict[str, Any]:
        """Parse raw string or dict output into normalized format.

        Args:
            raw_output: Raw JSON string or dictionary output.

        Returns:
            Normalized dictionary containing image semantic signals.
        """
        data: dict[str, Any] = {}
        if isinstance(raw_output, str):
            try:
                # Remove markdown code block fences if present
                clean_str = raw_output.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_str)
            except Exception:
                data = {"summary": raw_output, "classification": "Document"}
        elif isinstance(raw_output, dict):
            data = raw_output

        return {
            "summary": str(data.get("summary", "Processed image content.")),
            "classification": str(data.get("classification", "Unknown")),
            "entities": list(data.get("entities", [])),
            "dates": [str(d) for d in data.get("dates", [])],
            "times": [str(t) for t in data.get("times", [])],
            "amounts": [str(a) for a in data.get("amounts", [])],
            "people": [str(p) for p in data.get("people", [])],
            "organizations": [str(o) for o in data.get("organizations", [])],
            "locations": [str(l) for l in data.get("locations", [])],
            "urgency": str(data.get("urgency", "low")).lower(),
            "risk": str(data.get("risk", "low")).lower(),
            "confidence": float(data.get("confidence", 0.90)),
            "raw_output": data,
        }
