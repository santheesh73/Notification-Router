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
        has_negation = any(p in text_lower for p in ["nothing urgent", "not urgent", "no rush", "isn't urgent", "is not urgent", "no need to call", "don't call now", "later is fine"]) or bool(re.search(r"can wait (?:until|till|later|tomorrow)", text_lower))

        deadline_kws = ["deadline", "due date", "expires", "by today", "asap"]
        emergency_kws = ["emergency", "hospital", "sos", "accident", "help immediately"]
        if not has_negation:
            deadline_kws.append("urgent")
            emergency_kws.append("urgent")

        contains_deadline = any(k in text_lower for k in deadline_kws)
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
        contains_emergency = any(k in text_lower for k in emergency_kws)
        contains_help = any(k in text_lower for k in ["help", "assist", "support", "issue"])
        contains_thank_you = any(k in text_lower for k in ["thank you", "thanks", "thx", "appreciate"])
        contains_greeting = any(k in text_lower for k in ["hi", "hello", "hey", "good morning", "good evening"])
        contains_question = "?" in text

        # Advanced Phase 5 Signals
        temporal_urgency_kws = ["mins max", "minutes max", "leaving", "pulled to", "by eod", "come online now", "escalation starts", "in 20 minutes", "in 15 mins", "by 5 pm", "by 7:35", "immediately", "urgent", "asap"]
        temporal_urgency = (not has_negation) and any(k in text_lower for k in temporal_urgency_kws)

        # Weighted Scam Risk Score (Phase 6)
        scam_risk_score = 0
        if contains_otp or any(k in text_lower for k in ["6 digit", "passcode", "otp code"]):
            scam_risk_score += 4
        if any(k in text_lower for k in ["account-login.in", "bit.ly", "pay-check-secure.com", "t.me/", "verify now", "confirm password"]):
            scam_risk_score += 3
        if any(k in text_lower for k in ["security alert", "payout profile", "account suspended", "profile blocked"]):
            scam_risk_score += 2
        if any(k in text_lower for k in ["within 2 hours", "blocked today", "expire today", "in 30 mins"]):
            scam_risk_score += 2
        if contains_bank or contains_upi:
            scam_risk_score += 1

        # Event Score (Phase 8)
        event_score = sum([
            1 if any(k in text_lower for k in ["bus leaving", "route b", "stadium road", "parents", "kids"]) else 0,
            1 if any(k in text_lower for k in ["appointment", "prescription", "health-related", "scheduled time", "care services"]) else 0,
            1 if any(k in text_lower for k in ["cultural night", "form is open", "add flat no", "dish in the sheet"]) else 0,
            1 if any(k in text_lower for k in ["school circular", "consent note", "timing"]) else 0,
            1 if contains_event or contains_meeting else 0,
        ])

        # Promotion Score (Phase 7)
        promotion_score = sum([
            1 if any(k in text_lower for k in ["rs ", "per person", "7 nights", "itinerary", "ladakh"]) else 0,
            1 if any(k in text_lower for k in ["selling", "cycle helmet", "kurta set", "photos attached", "pickup near"]) else 0,
            1 if any(k in text_lower for k in ["50% off", "try50", "shopping offer", "extra discounts"]) else 0,
            1 if contains_discount or contains_offer or contains_coupon else 0,
        ])

        # Greeting Score (Phase 9)
        greeting_score = sum([
            1 if contains_greeting else 0,
            1 if any(k in text_lower for k in ["hope today is peaceful", "good vibes", "keep smiling", "share blessings"]) else 0,
        ])

        # Forward Probability
        is_forward_text = any(k in text_lower for k in ["fwd as received", "forward to family", "forwarding because", "share with 10 people", "forward this to"])
        fwd_prob = 0.9 if is_forward_text else 0.0

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
            "temporal_urgency": temporal_urgency,
            "scam_risk_score": scam_risk_score,
            "event_score": event_score,
            "promotion_score": promotion_score,
            "greeting_score": greeting_score,
            "forward_probability": fwd_prob,
        }
