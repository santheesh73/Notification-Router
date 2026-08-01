"""Safety & Security Feature Extractor."""

import re
from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor

# Shortened URL patterns
SHORTENED_DOMAINS: list[str] = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "buff.ly", "ow.ly"]


class SafetyFeatureExtractor(BaseFeatureExtractor):
    """Extracts security, scam risk, and fraud detection features using deterministic patterns."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract safety features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of safety and security feature signals.
        """
        text = str(message.get("text_content", "") or message.get("message_text", "") or "")
        text_lower = text.lower()

        # 1. Keyword Signal Detections
        scam_keywords = ["congratulations", "winner", "claim now", "urgent action required", "verify your account immediately", "bank security alert", "free gift", "prize"]
        contains_scam_keyword = any(k in text_lower for k in scam_keywords)

        lottery_keywords = ["lottery", "jackpot", "won $", "won ₹", "draw winner", "lucky spin"]
        contains_lottery = any(k in text_lower for k in lottery_keywords)

        crypto_keywords = ["bitcoin", "crypto", "usdt", "binance", "airdrop", "solana", "eth", "wallet address"]
        contains_crypto = any(k in text_lower for k in crypto_keywords)

        investment_keywords = ["guaranteed return", "100% profit", "investment scheme", "double your money", "forex trading", "high yield"]
        contains_investment = any(k in text_lower for k in investment_keywords)

        suspended_keywords = ["account suspended", "account blocked", "kyc expired", "deactivated within 24 hours", "action required"]
        contains_account_suspended = any(k in text_lower for k in suspended_keywords)

        verification_keywords = ["click to verify", "enter pin", "share otp", "login to continue", "verify identity"]
        contains_verification_request = any(k in text_lower for k in verification_keywords)

        # 2. Payment & Link Detections
        contains_unknown_payment = ("pay" in text_lower or "transfer" in text_lower) and ("http" in text_lower or "link" in text_lower)
        contains_shortened_url = any(dom in text_lower for dom in SHORTENED_DOMAINS)

        # Check for unknown domains or raw IPs in links
        raw_ip_link = bool(re.search(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", text))
        contains_unknown_domain = raw_ip_link or contains_shortened_url

        # 3. Calculate Deterministic Risk Score
        risk_signals = [
            contains_scam_keyword,
            contains_lottery,
            contains_crypto,
            contains_investment,
            contains_account_suspended,
            contains_verification_request,
            contains_unknown_payment,
            contains_shortened_url,
            contains_unknown_domain,
        ]

        active_signals_count = sum(1 for s in risk_signals if s)
        risk_score = round(min(1.0, active_signals_count * 0.25), 4)

        return {
            "contains_scam_keyword": contains_scam_keyword,
            "contains_lottery": contains_lottery,
            "contains_crypto": contains_crypto,
            "contains_investment": contains_investment,
            "contains_account_suspended": contains_account_suspended,
            "contains_verification_request": contains_verification_request,
            "contains_unknown_payment": contains_unknown_payment,
            "contains_shortened_url": contains_shortened_url,
            "contains_unknown_domain": contains_unknown_domain,
            "risk_score": risk_score,
        }
