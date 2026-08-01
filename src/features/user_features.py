"""User Feature Extractor."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class UserFeatureExtractor(BaseFeatureExtractor):
    """Extracts target user preference and engagement features directly from UserProfile."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract user features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of user feature signals.
        """
        user_id = str(message.get("recipient_id", message.get("user_id", "")))
        sender_id = str(message.get("sender_id", ""))
        group_id = str(message.get("group_id", "")) if str(message.get("group_id", "")) != "nan" and str(message.get("group_id", "")) != "" else None

        user_profile = context.get_user(user_id)

        if not user_profile:
            return {
                "reply_rate": 0.0,
                "open_rate": 0.0,
                "dismiss_rate": 0.0,
                "report_rate": 0.0,
                "notification_load": 0.0,
                "engagement_score": 0.0,
                "quiet_hours": False,
                "muted_group": False,
                "favorite_contact": False,
                "favorite_business": False,
            }

        muted_group = group_id in user_profile.muted_groups if group_id else False
        favorite_contact = sender_id in user_profile.trusted_contacts
        favorite_business = sender_id in user_profile.favorite_businesses

        quiet_hours = bool(user_profile.quiet_hours_start and user_profile.quiet_hours_end)

        return {
            "reply_rate": user_profile.reply_rate,
            "open_rate": user_profile.open_rate,
            "dismiss_rate": user_profile.dismiss_rate,
            "report_rate": user_profile.report_rate,
            "notification_load": user_profile.notification_load,
            "engagement_score": user_profile.engagement_score,
            "quiet_hours": quiet_hours,
            "muted_group": muted_group,
            "favorite_contact": favorite_contact,
            "favorite_business": favorite_business,
        }
