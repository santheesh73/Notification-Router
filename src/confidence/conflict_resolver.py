"""Conflict Resolver for Decision Fusion Engine."""

from typing import Any

from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.rules.rule_result import RuleResult

VALID_ACTIONS: set[str] = {"notify", "digest", "mute"}

VALID_MESSAGE_TYPES: set[str] = {
    "personal", "urgent", "event", "payment", "business_update",
    "promotion", "greeting", "forward", "spam", "scam", "unknown"
}

TYPE_NORMALIZATION_MAP: dict[str, str] = {
    "business": "business_update",
    "office": "business_update",
    "family": "personal",
    "duplicate": "spam",
    "reminder": "event",
    "transaction": "payment",
    "phishing": "scam",
}


class ConflictResolver:
    """Resolves potential action and category conflicts between Rule Engine and LLM output."""

    def resolve(
        self,
        rule_result: RuleResult,
        llm_result: DecisionResult,
        media_result: MediaResult | None,
        vector: FeatureVector,
    ) -> tuple[str, str, str, str, bool]:
        """Resolve final action, message_type, reason, decision_source, and ai_resolved flag.

        Hierarchy:
            1. Multimodal Emergency Hazard Override (OCR / Speech critical alert)
            2. Resolved Rule Engine Decision Precedence (Scam, Payment, Muted Group, Office, Personal, Urgent, etc.)
            3. LLM Router Decision (for unresolved messages)
            4. Deterministic Feature Vector Fallback

        Returns:
            Tuple of (action, message_type, reason, decision_source, ai_resolved).
        """
        # 1. Multimodal Hazard Override
        if media_result and getattr(media_result, "processed", False):
            is_urg = getattr(media_result, "is_urgent", False)
            urg_lvl = str(getattr(media_result, "urgency", getattr(media_result, "urgency_level", "NORMAL"))).upper()
            if is_urg or "CRITICAL" in urg_lvl or "HIGH" in urg_lvl:
                action = "notify"
                msg_type = "urgent"
                reason = "Multimodal hazard or emergency alert detected in attachment (OCR/Transcript)."
                return action, msg_type, reason, "MultimodalManager", True

        # 2. Rule Engine Resolved Decision Precedence
        if rule_result and rule_result.resolved and rule_result.action not in ("unresolved", "unknown", ""):
            action = self._sanitize_action(rule_result.action)
            msg_type = self._normalize_type(rule_result.message_type)
            reason = self._build_contextual_reason(vector, msg_type, action)
            rule_name = getattr(rule_result, "triggered_rule", getattr(rule_result, "rule_triggered", "Rule"))
            return action, msg_type, reason, f"RuleEngine:{rule_name}", False

        # 3. LLM Router Decision for Unresolved Messages
        if llm_result and llm_result.provider not in ("RuleEngine", "Rule Engine Fallback") and llm_result.confidence > 0.50:
            action = self._sanitize_action(llm_result.action)
            msg_type = self._normalize_type(llm_result.message_type)
            reason = llm_result.reason or self._build_contextual_reason(vector, msg_type, action)
            return action, msg_type, reason, f"LLM:{llm_result.provider}", True

        # 4. Deterministic Feature Vector Fallback
        inferred_type = self._infer_type_from_vector(vector)
        action = "digest" if inferred_type in ("business_update", "event", "promotion") else ("notify" if inferred_type in ("personal", "urgent", "payment") else "mute")
        reason = self._build_contextual_reason(vector, inferred_type, action)
        return action, inferred_type, reason, "DeterministicFallback", False

    def _sanitize_action(self, action: str) -> str:
        """Sanitize action string to valid set."""
        act = str(action).lower().strip()
        if act in VALID_ACTIONS:
            return act
        return "digest"

    def _normalize_type(self, message_type: str) -> str:
        """Normalize message_type to competition specification."""
        if not message_type or message_type in ("", "unknown"):
            return "unknown"
        if message_type in VALID_MESSAGE_TYPES:
            return message_type
        return TYPE_NORMALIZATION_MAP.get(message_type, "unknown")

    def _build_contextual_reason(self, vector: FeatureVector, msg_type: str, action: str) -> str:
        """Generate entity-grounded contextual reason using real sender_user_id, business_id, or group_id."""
        sender = str(getattr(vector, "sender_id", "") or "").strip()
        grp = str(getattr(vector, "group_id", "") or "").strip()
        biz = str(getattr(vector, "business_id", "") or "").strip()

        if sender in ("USR_UNKNOWN", "nan", "None"):
            sender = ""
        if grp in ("nan", "None"):
            grp = ""
        if biz in ("nan", "None"):
            biz = ""

        # Construct natural entity clause without stuffing message_id or placeholder strings
        if biz:
            entity_clause = f"from business {biz}"
        elif grp and sender:
            entity_clause = f"from sender {sender} in group {grp}"
        elif sender:
            entity_clause = f"from sender {sender}"
        elif grp:
            entity_clause = f"in group {grp}"
        else:
            entity_clause = ""

        clause_space = f" {entity_clause}" if entity_clause else ""

        if msg_type == "scam":
            return f"Phishing risk or security threat detected{clause_space}."
        elif msg_type == "payment":
            trust_flag = " (verified provider)" if (vector.verified or vector.trusted_business) else ""
            return f"Financial transaction or payment alert{clause_space}{trust_flag}."
        elif msg_type == "business_update":
            return f"Operational notification{clause_space} routed to {action}."
        elif msg_type == "personal":
            return f"Direct personal communication{clause_space} routed to {action}."
        elif msg_type == "urgent":
            return f"Time-sensitive alert{clause_space} requiring immediate user attention."
        elif msg_type == "event":
            return f"Event schedule update{clause_space} routed to {action}."
        elif msg_type == "forward":
            fwd_cnt = getattr(vector, "forwarded_count", 1)
            return f"Broadcast message ({fwd_cnt}x forwards){clause_space} routed to {action}."
        elif msg_type == "spam":
            return f"Unsolicited broadcast content{clause_space} muted."
        elif msg_type == "promotion":
            return f"Marketing update{clause_space} routed to summary {action}."
        elif msg_type == "greeting":
            return f"Social greeting{clause_space} routed to {action}."
        else:
            return f"Contextual message{clause_space} routed to {action} based on multi-signal analysis."

    def _infer_type_from_vector(self, vector: FeatureVector) -> str:
        """Infer best message type from feature vector when classification is missing."""
        if getattr(vector, "contains_scam_keyword", False):
            return "scam"
        if getattr(vector, "contains_payment", False) or getattr(vector, "contains_invoice", False):
            return "payment"
        has_urg = getattr(vector, "contains_urgent_keyword", False) or getattr(vector, "is_urgent", False) or getattr(vector, "contains_deadline", False)
        if has_urg or getattr(vector, "during_quiet_hours", False):
            return "urgent"
        if getattr(vector, "is_forwarded", False) and getattr(vector, "forwarded_count", 0) > 3:
            return "spam"
        if getattr(vector, "group_type", "") == "office" or getattr(vector, "trusted_business", False):
            return "business_update"
        if getattr(vector, "trusted_sender", False):
            return "personal"
        return "business_update"
