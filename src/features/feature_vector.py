"""FeatureVector Data Model for WhatsApp Message Notification Router."""

from dataclasses import dataclass


@dataclass
class FeatureVector:
    """Dataclass holding all extracted feature signals for an incoming message."""

    # 1. Core Metadata
    message_id: str
    user_id: str
    conversation_type: str  # "personal", "group", "business"
    sender_id: str
    group_id: str | None = None
    business_id: str | None = None
    timestamp: str | None = None
    media_type: str | None = None  # "text", "image", "voice", etc.
    forwarded_count: int = 0
    message_text: str = ""

    # 2. Text Features
    message_length: int = 0
    word_count: int = 0
    sentence_count: int = 0
    contains_url: bool = False
    contains_email: bool = False
    contains_phone: bool = False
    contains_money: bool = False
    contains_currency: bool = False
    contains_payment: bool = False
    contains_invoice: bool = False
    contains_discount: bool = False
    contains_coupon: bool = False
    contains_offer: bool = False
    contains_deadline: bool = False
    contains_date: bool = False
    contains_time: bool = False
    contains_meeting: bool = False
    contains_exam: bool = False
    contains_assignment: bool = False
    contains_event: bool = False
    contains_location: bool = False
    contains_bank: bool = False
    contains_otp: bool = False
    contains_upi: bool = False
    contains_qr: bool = False
    contains_link: bool = False
    contains_password: bool = False
    contains_emergency: bool = False
    contains_help: bool = False
    contains_thank_you: bool = False
    contains_greeting: bool = False
    contains_question: bool = False
    uppercase_ratio: float = 0.0
    emoji_count: int = 0
    punctuation_ratio: float = 0.0
    language_hint: str = "en"

    # 3. Conversation Features
    personal: bool = False
    group: bool = False
    business: bool = False
    is_forwarded: bool = False
    forward_level: int = 0
    has_media: bool = False

    # 4. Sender Features
    trusted_sender: bool = False
    trusted_business: bool = False
    trusted_group: bool = False
    new_sender: bool = False
    reply_history: int = 0
    interaction_frequency: float = 0.0
    report_history: int = 0
    blocked_history: bool = False

    # 5. User Features
    reply_rate: float = 0.0
    open_rate: float = 0.0
    dismiss_rate: float = 0.0
    report_rate: float = 0.0
    notification_load: float = 0.0
    engagement_score: float = 0.0
    quiet_hours: bool = False
    muted_group: bool = False
    favorite_contact: bool = False
    favorite_business: bool = False

    # 6. Group Features
    group_type: str = "Other"
    member_count: int = 0
    activity_score: float = 0.0
    importance_score: float = 0.0
    user_participation: int = 0
    mute_state: bool = False

    # 7. Business Features
    verified: bool = False
    trust_score: float = 0.0
    orders: int = 0
    payments: int = 0
    bookings: int = 0
    subscriptions: int = 0
    opt_in: bool = True
    opt_out: bool = False
    interaction_count: int = 0

    # 8. Temporal Features
    hour_of_day: int = 12
    day_of_week: int = 0
    weekend: bool = False
    night: bool = False
    during_quiet_hours: bool = False
    working_hours: bool = True
    holiday_flag: bool = False

    # 9. Safety & Advanced Features (Phase 5)
    contains_scam_keyword: bool = False
    contains_lottery: bool = False
    contains_crypto: bool = False
    contains_investment: bool = False
    contains_account_suspended: bool = False
    contains_verification_request: bool = False
    contains_unknown_payment: bool = False
    contains_shortened_url: bool = False
    contains_unknown_domain: bool = False
    risk_score: float = 0.0
    temporal_urgency: bool = False
    scam_risk_score: int = 0
    event_score: int = 0
    promotion_score: int = 0
    greeting_score: int = 0
    forward_probability: float = 0.0
    duplicate_probability: float = 0.0
    personal_familiarity_score: float = 0.0
    business_verification_score: float = 0.0
    historical_interaction_frequency: float = 0.0
