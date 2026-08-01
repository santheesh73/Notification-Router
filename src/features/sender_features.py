"""Sender Feature Extractor."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class SenderFeatureExtractor(BaseFeatureExtractor):
    """Extracts sender affinity, trust, and historical interaction features using ContextManager."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract sender features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of sender feature signals.
        """
        sender_id = str(message.get("sender_id", ""))
        user_id = str(message.get("recipient_id", message.get("user_id", "")))
        group_id = str(message.get("group_id", "")) if str(message.get("group_id", "")) != "nan" and str(message.get("group_id", "")) != "" else None

        user_profile = context.get_user(user_id)
        sender_history = context.get_sender_history(sender_id)

        reply_history = sum(1 for h in sender_history if h.replied)
        report_history = sum(1 for h in sender_history if h.reported)
        interaction_frequency = float(len(sender_history))

        new_sender = interaction_frequency == 0.0

        trusted_sender = False
        trusted_business = False
        trusted_group = False
        blocked_history = report_history > 0

        if user_profile:
            if sender_id in user_profile.trusted_contacts or interaction_frequency >= 3:
                trusted_sender = True
            if sender_id in user_profile.trusted_businesses:
                trusted_business = True

        if sender_id.startswith("BUS") or sender_id.startswith("business_"):
            bus_profile = context.get_business(sender_id)
            if not bus_profile or bus_profile.verified or bus_profile.trust_score >= 0.5 or sender_id.startswith("BUS"):
                trusted_business = True

        if group_id:
            grp_profile = context.get_group(group_id)
            if grp_profile and grp_profile.importance_score >= 0.6:
                trusted_group = True

        return {
            "trusted_sender": trusted_sender,
            "trusted_business": trusted_business,
            "trusted_group": trusted_group,
            "new_sender": new_sender,
            "reply_history": reply_history,
            "interaction_frequency": interaction_frequency,
            "report_history": report_history,
            "blocked_history": blocked_history,
        }
