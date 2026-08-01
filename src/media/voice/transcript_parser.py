"""Audio Transcript Semantic Parser."""

import re
from typing import Any


class TranscriptParser:
    """Parses audio transcripts into structured semantic signals for MediaResult."""

    def parse(self, transcript_data: dict[str, Any]) -> dict[str, Any]:
        """Parse transcript text into structured dictionary.

        Args:
            transcript_data: Dictionary output from AudioModel.

        Returns:
            Normalized dictionary containing voice semantic extraction.
        """
        text = str(transcript_data.get("text", ""))
        text_lower = text.lower()

        # Classification inference
        classification = "Action Request"
        if "meeting" in text_lower or "call" in text_lower:
            classification = "Meeting"
        elif "reminder" in text_lower or "due" in text_lower:
            classification = "Reminder"
        elif "pay" in text_lower or "money" in text_lower or "invoice" in text_lower:
            classification = "Payment"
        elif "hi" in text_lower or "hello" in text_lower or "morning" in text_lower:
            classification = "Greeting"
        elif "emergency" in text_lower or "urgent" in text_lower or "hospital" in text_lower:
            classification = "Emergency"
        elif "lottery" in text_lower or "crypto" in text_lower or "scam" in text_lower:
            classification = "Scam"
        elif "discount" in text_lower or "offer" in text_lower:
            classification = "Promotion"

        # Regex extractions
        dates = re.findall(r"\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text_lower)
        times = re.findall(r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b", text_lower)
        amounts = re.findall(r"\$\d+|\d+\s*dollars|₹\d+|\d+\s*rupees", text_lower)

        urgency = "high" if "urgent" in text_lower or "emergency" in text_lower else "medium"
        risk = "high" if classification == "Scam" else "low"

        return {
            "summary": text if text else "Voice message transcription.",
            "classification": classification,
            "entities": ["voice_note", classification.lower()],
            "dates": dates,
            "times": times,
            "amounts": amounts,
            "people": [],
            "organizations": [],
            "locations": [],
            "urgency": urgency,
            "risk": risk,
            "confidence": float(transcript_data.get("confidence", 0.90)),
            "raw_output": transcript_data,
        }
