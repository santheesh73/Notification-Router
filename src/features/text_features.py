"""Text Feature Extractor."""

import re
from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class TextFeatureExtractor(BaseFeatureExtractor):
    """Extracts linguistic, structural, and semantic text features from messages."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract text features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of extracted text feature signals.
        """
        text = str(message.get("text_content", "") or message.get("message_text", "") or "")
        text_lower = text.lower()

        # Structural metrics
        msg_len = len(text)
        words = text.split()
        word_count = len(words)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        sentence_count = max(1 if text.strip() else 0, len(sentences))

        # Ratios
        uppercase_chars = sum(1 for c in text if c.isupper())
        uppercase_ratio = round(uppercase_chars / max(1, msg_len), 4)

        punctuation_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        punctuation_ratio = round(punctuation_chars / max(1, msg_len), 4)

        # Basic emoji detection (unicode range check)
        emoji_count = len(re.findall(r"[\U00010000-\U0010ffff]", text))

        # Regex patterns
        url_pattern = r"https?://\S+|www\.\S+"
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        phone_pattern = r"\+?\d[\d -]{7,}\d"
        money_pattern = r"\$|\bUSD\b|\bEUR\b|\bINR\b|₹|\bRs\.?\b|\bdollars?\b"
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}\b"
        time_pattern = r"\b\d{1,2}:\d{2}(?:\s?[ap]\.?m\.?)?\b"
        otp_pattern = r"\b\d{4,8}\b|\bOTP\b|\bcode\b"

        # Signal checks
        contains_url = bool(re.search(url_pattern, text, re.IGNORECASE))
        contains_link = contains_url or "http" in text_lower or "link" in text_lower
        contains_email = bool(re.search(email_pattern, text, re.IGNORECASE))
        contains_phone = bool(re.search(phone_pattern, text))
        contains_money = bool(re.search(money_pattern, text, re.IGNORECASE))
        contains_currency = contains_money

        contains_payment = any(k in text_lower for k in ["payment", "pay", "paid", "transfer", "remit", "razorpay", "stripe", "gpay", "phonepe", "paytm"])
        contains_invoice = any(k in text_lower for k in ["invoice", "receipt", "bill", "statement"])
        contains_discount = any(k in text_lower for k in ["discount", "off", "sale", "save"])
        contains_coupon = any(k in text_lower for k in ["coupon", "promo", "voucher", "code"])
        contains_offer = any(k in text_lower for k in ["offer", "deal", "cashback", "bonus"])
        contains_deadline = any(k in text_lower for k in ["deadline", "due date", "expires", "urgent", "by today", "asap"])
        contains_date = bool(re.search(date_pattern, text, re.IGNORECASE))
        contains_time = bool(re.search(time_pattern, text, re.IGNORECASE))
        contains_meeting = any(k in text_lower for k in ["meeting", "zoom", "teams", "google meet", "call", "sync", "standup"])
        contains_exam = any(k in text_lower for k in ["exam", "test", "quiz", "midterm", "final"])
        contains_assignment = any(k in text_lower for k in ["assignment", "homework", "submission", "task"])
        contains_event = any(k in text_lower for k in ["event", "webinar", "conference", "party", "birthday"])
        contains_location = any(k in text_lower for k in ["location", "address", "venue", "map", "directions"])
        contains_bank = any(k in text_lower for k in ["bank", "account", "credit card", "debit card", "atm", "branch"])
        contains_otp = any(k in text_lower for k in ["otp", "verification code", "one time password", "passcode"]) or bool(re.search(otp_pattern, text, re.IGNORECASE))
        contains_upi = any(k in text_lower for k in ["upi", "@okicici", "@okaxis", "@ybl", "@paytm", "vpa"])
        contains_qr = any(k in text_lower for k in ["qr code", "qr", "scan"])
        contains_password = any(k in text_lower for k in ["password", "pin", "credentials", "login"])
        contains_emergency = any(k in text_lower for k in ["emergency", "urgent", "hospital", "sos", "accident", "help immediately"])
        contains_help = any(k in text_lower for k in ["help", "assist", "support", "issue"])
        contains_thank_you = any(k in text_lower for k in ["thank you", "thanks", "thx", "appreciate"])
        contains_greeting = any(k in text_lower for k in ["hi", "hello", "hey", "good morning", "good evening"])
        contains_question = "?" in text

        return {
            "message_length": msg_len,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "contains_url": contains_url,
            "contains_email": contains_email,
            "contains_phone": contains_phone,
            "contains_money": contains_money,
            "contains_currency": contains_currency,
            "contains_payment": contains_payment,
            "contains_invoice": contains_invoice,
            "contains_discount": contains_discount,
            "contains_coupon": contains_coupon,
            "contains_offer": contains_offer,
            "contains_deadline": contains_deadline,
            "contains_date": contains_date,
            "contains_time": contains_time,
            "contains_meeting": contains_meeting,
            "contains_exam": contains_exam,
            "contains_assignment": contains_assignment,
            "contains_event": contains_event,
            "contains_location": contains_location,
            "contains_bank": contains_bank,
            "contains_otp": contains_otp,
            "contains_upi": contains_upi,
            "contains_qr": contains_qr,
            "contains_link": contains_link,
            "contains_password": contains_password,
            "contains_emergency": contains_emergency,
            "contains_help": contains_help,
            "contains_thank_you": contains_thank_you,
            "contains_greeting": contains_greeting,
            "contains_question": contains_question,
            "uppercase_ratio": uppercase_ratio,
            "emoji_count": emoji_count,
            "punctuation_ratio": punctuation_ratio,
            "language_hint": "en",
        }
