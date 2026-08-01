"""Scam & Phishing Detection Rule."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.base_rule import BaseRule
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult

SCAM_KEYWORDS = {
    "otp",
    "account block",
    "account lock",
    "profile band",
    "profile locked",
    "verification nahi",
    "clearance amount",
    "claim benefits",
    "loan approved",
    "reactivation fee",
    "share otp",
    "restore access",
    "urgent service",
    "pending charge",
    "lottery",
    "crypto",
    "investment",
    "account suspended",
}


class ScamRule(BaseRule):
    """Detects fraudulent, phishing, lottery, and scam messages (Priority: CRITICAL)."""

    def __init__(self) -> None:
        super().__init__(name="ScamRule", priority=RulePriority.CRITICAL)

    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        if not self.enabled:
            return None

        is_scam = (
            vector.contains_scam_keyword
            or vector.contains_lottery
            or vector.contains_crypto
            or vector.contains_investment
            or vector.contains_account_suspended
            or vector.contains_verification_request
            or vector.contains_unknown_payment
            or vector.contains_unknown_domain
            or vector.contains_otp
            or vector.risk_score >= 0.4
        )

        # Additional keyword check
        text_content = getattr(vector, "message_text", "") or ""
        if not is_scam and text_content:
            lower_txt = str(text_content).lower()
            if any(kw in lower_txt for kw in SCAM_KEYWORDS):
                is_scam = True

        if is_scam:
            # Build contextual reason
            text_lower = str(text_content).lower()
            if vector.contains_otp or "otp" in text_lower:
                reason = "Possible phishing attempt requesting OTP or login credentials."
            elif vector.contains_account_suspended or "account block" in text_lower or "account lock" in text_lower:
                reason = "Account suspension scam threatening access restriction."
            elif "loan approved" in text_lower or "claim benefits" in text_lower:
                reason = "Financial fraud offering unauthorized loans or benefits."
            elif vector.contains_unknown_domain or "bit.ly" in text_lower:
                reason = "Suspicious shortened URL from untrusted domain detected."
            elif "clearance amount" in text_lower or "pending charge" in text_lower or "reactivation fee" in text_lower:
                reason = "Fraudulent payment demand with urgency pressure tactics."
            elif vector.risk_score >= 0.6:
                reason = "High risk score triggered by multiple fraud signal indicators."
            elif vector.contains_verification_request:
                reason = "Unsolicited verification request from unverified sender."
            else:
                reason = "Detected fraudulent scam pattern with phishing indicators."

            return RuleResult(
                message_id=vector.message_id,
                resolved=True,
                action="mute",
                message_type="scam",
                reason=reason,
                confidence=0.98,
                triggered_rule=self.name,
                priority=str(self.priority),
                requires_ai=False,
            )

        return None
