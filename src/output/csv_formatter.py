"""CSV Formatter for Final Decisions."""

from typing import Any

from src.confidence.final_decision import FinalDecision


class CSVFormatter:
    """Formats FinalDecision dataclasses into dictionaries matching output.csv schema."""

    COLUMNS: list[str] = [
        "message_id",
        "action",
        "message_type",
        "reason",
        "confidence",
        "evidence_message_ids",
    ]

    def format_decision(self, decision: FinalDecision) -> dict[str, Any]:
        """Format a single FinalDecision into CSV row dictionary.

        Args:
            decision: FinalDecision instance.

        Returns:
            Formatted dictionary with keys matching CSV columns.
        """
        # Format evidence_message_ids as semicolon-separated string or 'none'
        if decision.evidence_message_ids and len(decision.evidence_message_ids) > 0:
            evidence_str = ";".join([str(eid) for eid in decision.evidence_message_ids if str(eid).strip()])
            if not evidence_str:
                evidence_str = "none"
        else:
            evidence_str = "none"

        # Sanitize reason text (no double quotes breaking CSV)
        clean_reason = decision.reason.replace('"', "'").strip()

        return {
            "message_id": decision.message_id,
            "action": decision.action,
            "message_type": decision.message_type,
            "reason": clean_reason,
            "confidence": round(float(decision.confidence), 4),
            "evidence_message_ids": evidence_str,
        }
