"""Structured Prompt Builder for Multi-LLM Providers."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult


class PromptBuilder:
    """Standardized Prompt Builder formatting identical structured prompts across all LLM providers."""

    SYSTEM_INSTRUCTION: str = (
        "=== SYSTEM ROLE ===\n"
        "You are an expert AI Notification Router for a WhatsApp messaging app.\n"
        "Your task is to classify an incoming message and decide whether to notify the user immediately, "
        "include it in a periodic digest, or mute it completely.\n\n"
        "=== Required Output Schema ===\n"
        "Return ONLY a single valid JSON object. Do NOT wrap in markdown syntax (no ```json). Do NOT add explanations.\n\n"
        "JSON SCHEMA:\n"
        "{\n"
        '    "action": "notify|digest|mute",\n'
        '    "message_type": "personal|urgent|event|payment|business_update|promotion|greeting|forward|spam|scam|unknown",\n'
        '    "reason": "<short explanation>",\n'
        '    "confidence": 0.91\n'
        "}\n\n"
        "=== DECISION INSTRUCTIONS ===\n"
        "- notify: Urgent messages, direct payment requests, security alerts, high-priority group alerts.\n"
        "- digest: General updates, social chatter, routine business announcements, low-priority events.\n"
        "- mute: Spam, scams, promotional broadcasts, muted group chatter, repetitive advertisements.\n"
        "Never return markdown. Never return explanations. Only JSON.\n"
    )

    @classmethod
    def build_prompt(
        cls,
        vector: FeatureVector,
        rule_result: RuleResult,
        context: ContextManager | None = None,
        media_result: MediaResult | None = None,
        retrieval_result: RetrievalResult | None = None,
    ) -> str:
        """Construct identical structured prompt for an incoming message.

        Args:
            vector: FeatureVector instance.
            rule_result: RuleResult instance.
            context: ContextManager instance.
            media_result: Optional MediaResult instance.
            retrieval_result: Optional RetrievalResult instance.

        Returns:
            Formatted prompt string.
        """
        sender_id = getattr(vector, "sender_id", "unknown_sender")
        user_id = getattr(vector, "user_id", None) or getattr(vector, "recipient_id", "u_001")
        group_id = getattr(vector, "group_id", None)
        business_id = getattr(vector, "business_id", None)
        raw_text = (
            getattr(vector, "text_content", None)
            or getattr(vector, "text", None)
            or getattr(vector, "message_text", None)
            or ""
        )

        # Sender Context
        sender_profile = context.get_user(sender_id) if context else None
        sender_type = "Group Member" if group_id else ("Known Contact" if sender_profile else "Unknown Sender")

        # Group Context
        group_profile = context.get_group(group_id) if (context and group_id) else None
        if group_profile:
            g_name = getattr(group_profile, "group_name", getattr(group_profile, "name", f"Group {group_id}"))
            g_type = getattr(group_profile, "group_type", "Other")
            group_desc = f"{g_name} (type={g_type})"
        else:
            group_desc = "Direct Message" if not group_id else f"Group {group_id}"

        # Business Context
        business_profile = context.get_business(business_id) if (context and business_id) else None
        if business_profile:
            b_name = getattr(business_profile, "brand_name", getattr(business_profile, "name", str(business_id)))
            business_desc = f"{b_name}"
        else:
            business_desc = str(business_id) if business_id else "None"

        # Media Summary
        media_summary = "None"
        if media_result and getattr(media_result, "processed", False):
            m_type = getattr(media_result, "media_type", "media")
            m_cls = getattr(media_result, "classification", "general")
            m_txt = getattr(media_result, "extracted_text", "") or "Visual content processed"
            media_summary = f"[{str(m_type).upper()}] Classification: {m_cls}, Summary: {m_txt}"

        # Safety Flags
        safety_flags = []
        if getattr(vector, "muted_group", False) or getattr(vector, "mute_state", False):
            safety_flags.append("MUTED_GROUP")
        if (
            getattr(vector, "contains_scam_keyword", False)
            or "spam" in (getattr(rule_result, "triggered_rule", "") or "").lower()
            or "scam" in (getattr(rule_result, "triggered_rule", "") or "").lower()
        ):
            safety_flags.append("SPAM_SCAM_KEYWORDS")
        if getattr(vector, "contains_urgency", False) or getattr(vector, "has_urgency_keywords", False):
            safety_flags.append("URGENT_KEYWORDS")
        safety_str = ", ".join(safety_flags) if safety_flags else "None"

        # Evidence / Historical Messages Summary
        evidence_str = "None"
        hist_str = "None"
        if retrieval_result and getattr(retrieval_result, "evidence_message_ids", None):
            evidence_str = f"Similar historical IDs: {', '.join(retrieval_result.evidence_message_ids[:3])}"
            hist_str = f"Count={len(retrieval_result.evidence_message_ids)}"

        prompt = (
            f"{cls.SYSTEM_INSTRUCTION}\n"
            f"=== FEATURE VECTOR FACTS ===\n"
            f"Incoming Message ID: {getattr(vector, 'message_id', 'unknown')}\n"
            f"Incoming Message Text: \"{raw_text or '[No Text Content]'}\"\n"
            f"Sender Context: ID={sender_id}, Type={sender_type}\n"
            f"User Context: Recipient={user_id}, Quiet Hours Active={getattr(vector, 'quiet_hours_active', False)}\n"
            f"Group Context: {group_desc}\n"
            f"Business Context: {business_desc}\n"
            f"Media Summary: {media_summary}\n"
            f"Safety Flags: {safety_str}\n"
            f"Evidence: {evidence_str}\n"
            f"Historical Messages: {hist_str}\n"
            f"Rule Engine Signal: Action={getattr(rule_result, 'action', 'unresolved')}, "
            f"Type={getattr(rule_result, 'message_type', 'unknown')}, "
            f"Confidence={getattr(rule_result, 'confidence', 0.0):.2f}, "
            f"Rule={getattr(rule_result, 'triggered_rule', 'None')}\n\n"
            f"=== Required Output Schema ==="
        )
        return prompt
