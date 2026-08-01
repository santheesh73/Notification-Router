"""Conflict Resolver for multi-source routing signals."""

from src.confidence.validation import TYPE_NORMALIZATION_MAP, VALID_MESSAGE_TYPES
from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


class ConflictResolver:
    """Deterministic Conflict Resolver enforcing decision priority hierarchy."""

    def resolve(
        self,
        rule_result: RuleResult,
        llm_result: DecisionResult,
        media_result: MediaResult | None,
        vector: FeatureVector,
    ) -> tuple[str, str, str, str, bool]:
        """Resolve conflicts between Rule Engine, LLM, Media, and Features.

        Args:
            rule_result: RuleResult from Phase 4.
            llm_result: DecisionResult from Phase 7.
            media_result: MediaResult from Phase 6 or None.
            vector: FeatureVector from Phase 3.

        Returns:
            Tuple of (action, message_type, reason, decision_source, resolved_by_ai).
        """
        # 1. Critical Safety & Emergency Override (Critical Rules: Priority 1)
        if rule_result.resolved and rule_result.priority == "RulePriority.CRITICAL":
            logger.debug(f"ConflictResolver: Preserving CRITICAL rule '{rule_result.triggered_rule}'.")
            return (
                rule_result.action,
                self._normalize_type(rule_result.message_type),
                rule_result.reason,
                "RULE_ENGINE",
                False,
            )

        # 2. Multimodal Emergency / Scam Safety Override
        if media_result and media_result.processed:
            if media_result.classification in ["Emergency", "Exams", "Meeting"] and media_result.urgency in ["high", "critical"]:
                logger.info(f"ConflictResolver: Overriding with Media Emergency signal '{media_result.classification}'.")
                return (
                    "notify",
                    "urgent" if media_result.classification == "Emergency" else "event",
                    f"Multimodal {media_result.classification.lower()} alert detected in media attachment.",
                    "FUSED",
                    True,
                )
            elif media_result.classification == "Scam" or media_result.risk == "high":
                logger.info("ConflictResolver: Overriding with Media Scam risk signal.")
                return (
                    "mute",
                    "scam",
                    "High risk scam signal detected in media attachment.",
                    "FUSED",
                    True,
                )

        # 3. Rule Engine Match for Deterministically Resolved Messages
        if rule_result.resolved and not rule_result.requires_ai:
            msg_type = self._normalize_type(rule_result.message_type)
            return (
                rule_result.action,
                msg_type,
                rule_result.reason,
                "RULE_ENGINE",
                False,
            )

        # 4. LLM / AI Decision for AI-routed ambiguous messages
        if llm_result and llm_result.provider not in ("RuleEngine", "None", "Mock"):
            msg_type = self._normalize_type(llm_result.message_type)
            reason = llm_result.reason

            # Sanitize reason — never reference Gemini or quota exhaustion
            if not reason or "gemini" in reason.lower() or "quota" in reason.lower():
                reason = self._build_contextual_reason(vector, msg_type, llm_result.action)

            return (
                llm_result.action,
                msg_type,
                reason,
                "LLM",
                True,
            )

        # 5. Fallback Decision — with inferred type (never "unknown" if possible)
        fallback_type = self._infer_type_from_vector(vector)
        fallback_reason = self._build_contextual_reason(vector, fallback_type, "digest")
        return (
            "digest",
            fallback_type,
            fallback_reason,
            "FALLBACK",
            False,
        )

    def _normalize_type(self, message_type: str) -> str:
        """Normalize message_type to competition-allowed values.

        Args:
            message_type: Raw message type string.

        Returns:
            Normalized message type string.
        """
        if not message_type or message_type in ("", "unknown"):
            return "unknown"
        if message_type in VALID_MESSAGE_TYPES:
            return message_type
        return TYPE_NORMALIZATION_MAP.get(message_type, "unknown")

    def _build_contextual_reason(self, vector: FeatureVector, msg_type: str, action: str) -> str:
        """Generate contextual reason based on vector features and message type.

        Args:
            vector: FeatureVector instance.
            msg_type: Resolved message type.
            action: Resolved action.

        Returns:
            Contextual reason string.
        """
        parts = []

        # Type-specific context
        if msg_type == "scam":
            parts.append("Suspicious content with fraud indicators")
        elif msg_type == "payment":
            if vector.trusted_business or vector.verified:
                parts.append("Trusted payment notification from verified provider")
            else:
                parts.append("Payment or financial transaction notification")
        elif msg_type == "business_update":
            if vector.verified:
                parts.append("Verified business update")
            else:
                parts.append("Business or organizational notification")
        elif msg_type == "personal":
            if vector.trusted_sender or vector.favorite_contact:
                parts.append("Message from trusted personal contact")
            else:
                parts.append("Personal message")
        elif msg_type == "urgent":
            parts.append("Time-sensitive message requiring immediate attention")
        elif msg_type == "event":
            parts.append("Event or scheduling notification")
        elif msg_type == "promotion":
            parts.append("Marketing or promotional content")
        elif msg_type == "greeting":
            parts.append("Social greeting or pleasantry")
        elif msg_type == "forward":
            parts.append("Forwarded content from external source")
        elif msg_type == "spam":
            parts.append("Unsolicited or repetitive broadcast content")
        else:
            parts.append("Message classified by content analysis")

        # Add sender/history context
        if vector.trusted_sender:
            parts.append("from trusted sender")
        if vector.new_sender:
            parts.append("from new or unknown sender")
        if vector.interaction_frequency > 0.5:
            parts.append("with high interaction history")

        return ". ".join(parts) + "."

    def _infer_type_from_vector(self, vector: FeatureVector) -> str:
        """Infer best message type from feature vector when classification is missing.

        Args:
            vector: FeatureVector instance.

        Returns:
            Inferred message type string.
        """
        if vector.contains_scam_keyword or vector.risk_score > 0.3:
            return "scam"
        if vector.contains_payment or vector.contains_invoice:
            return "payment"
        if vector.contains_event or vector.contains_meeting:
            return "event"
        if vector.business or vector.conversation_type == "business":
            return "business_update"
        if vector.contains_greeting:
            return "greeting"
        if vector.is_forwarded or vector.forwarded_count > 2:
            return "forward"
        if vector.contains_offer or vector.contains_discount:
            return "promotion"
        if vector.personal or vector.conversation_type == "personal":
            return "personal"
        if vector.group or vector.conversation_type == "group":
            return "business_update"
        return "unknown"
