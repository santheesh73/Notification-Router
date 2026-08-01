"""BusinessProfile Data Model."""

from dataclasses import dataclass


@dataclass
class BusinessProfile:
    """Dataclass representing structured WhatsApp business profile context."""

    business_id: str
    brand_name: str
    verified: bool = False
    account_age: int = 0
    reports: int = 0
    orders: int = 0
    payments: int = 0
    bookings: int = 0
    subscriptions: int = 0
    opt_in: bool = True
    opt_out: bool = False
    interaction_count: int = 0
    trust_score: float = 0.0
