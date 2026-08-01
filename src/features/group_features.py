"""Group Feature Extractor."""

from typing import Any

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class GroupFeatureExtractor(BaseFeatureExtractor):
    """Extracts group metadata, participation, and importance features directly from GroupProfile."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract group features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of group feature signals.
        """
        group_id = str(message.get("group_id", "")) if str(message.get("group_id", "")) != "nan" and str(message.get("group_id", "")) != "" else None
        user_id = str(message.get("recipient_id", message.get("user_id", "")))

        if not group_id:
            return {
                "group_type": "None",
                "member_count": 0,
                "activity_score": 0.0,
                "importance_score": 0.0,
                "user_participation": 0,
                "mute_state": False,
            }

        group_profile = context.get_group(group_id)
        if not group_profile:
            return {
                "group_type": "Other",
                "member_count": 0,
                "activity_score": 0.0,
                "importance_score": 0.0,
                "user_participation": 0,
                "mute_state": False,
            }

        user_part = group_profile.user_participation.get(user_id, 0)
        is_muted = group_profile.mute_state.get(user_id, False)

        return {
            "group_type": group_profile.group_type,
            "member_count": group_profile.member_count,
            "activity_score": group_profile.activity_score,
            "importance_score": group_profile.importance_score,
            "user_participation": user_part,
            "mute_state": is_muted,
        }
