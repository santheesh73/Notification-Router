"""Business Feature Extractor."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class BusinessFeatureExtractor(BaseFeatureExtractor):
    """Extracts business account metadata and trust metrics directly from BusinessProfile."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract business features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of business feature signals.
        """
        sender_id = str(message.get("sender_id", ""))
        business_id = sender_id if sender_id.startswith("BUS") else None

        if not business_id:
            return {
                "verified": False,
                "trust_score": 0.0,
                "orders": 0,
                "payments": 0,
                "bookings": 0,
                "subscriptions": 0,
                "opt_in": True,
                "opt_out": False,
                "interaction_count": 0,
            }

        bus_profile = context.get_business(business_id)
        if not bus_profile:
            return {
                "verified": False,
                "trust_score": 0.0,
                "orders": 0,
                "payments": 0,
                "bookings": 0,
                "subscriptions": 0,
                "opt_in": True,
                "opt_out": False,
                "interaction_count": 0,
            }

        return {
            "verified": bus_profile.verified,
            "trust_score": bus_profile.trust_score,
            "orders": bus_profile.orders,
            "payments": bus_profile.payments,
            "bookings": bus_profile.bookings,
            "subscriptions": bus_profile.subscriptions,
            "opt_in": bus_profile.opt_in,
            "opt_out": bus_profile.opt_out,
            "interaction_count": bus_profile.interaction_count,
        }
