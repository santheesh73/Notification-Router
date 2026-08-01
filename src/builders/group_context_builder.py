"""Group Context Profile Builder."""

import pandas as pd

from src.builders.base_builder import BaseContextBuilder
from src.models.group_profile import GroupProfile
from src.utils.logger import logger

# Supported Group Types
GROUP_TYPES: list[str] = [
    "Family",
    "Office",
    "School",
    "Apartment",
    "Community",
    "Announcements",
    "Sports",
    "Other",
]


class GroupContextBuilder(BaseContextBuilder[GroupProfile]):
    """Builder for assembling GroupProfile contexts from datasets."""

    def _infer_group_type(self, name: str, is_announcement: bool = False) -> str:
        """Infer group category from group name and announcement flag.

        Args:
            name: Group name string.
            is_announcement: Boolean indicating announcement-only group.

        Returns:
            Inferred group type category string.
        """
        if is_announcement:
            return "Announcements"

        name_lower = name.lower()
        if any(k in name_lower for k in ["devops", "office", "work", "team", "project", "corp", "tech"]):
            return "Office"
        elif any(k in name_lower for k in ["family", "home", "relatives"]):
            return "Family"
        elif any(k in name_lower for k in ["school", "class", "college", "univ", "alumni"]):
            return "School"
        elif any(k in name_lower for k in ["flat", "apt", "apartment", "society", "resident"]):
            return "Apartment"
        elif any(k in name_lower for k in ["football", "cricket", "sports", "gym", "club"]):
            return "Sports"
        elif any(k in name_lower for k in ["community", "neighborhood", "volunteers"]):
            return "Community"

        return "Other"

    def build(self) -> dict[str, GroupProfile]:
        """Build GroupProfile for every group in the repository.

        Returns:
            Dictionary mapping group_id -> GroupProfile.
        """
        groups_df = self.get_dataset("groups")
        members_df = self.get_dataset("group_members")
        history_df = self.get_dataset("message_history")

        if groups_df.empty:
            logger.warning("No group records found in repository.")
            return {}

        profiles: dict[str, GroupProfile] = {}

        for _, row in groups_df.iterrows():
            group_id = str(row["group_id"])
            group_name = str(row.get("group_name", f"Group_{group_id}"))
            is_announcement = bool(row.get("is_announcement_only", False))

            # 1. Infer Group Type
            g_type = self._infer_group_type(group_name, is_announcement)

            # 2. Member & Admin Counts + Mute Map
            admin_count = 0
            member_count = int(row.get("member_count", 0))
            mute_map: dict[str, bool] = {}

            if not members_df.empty and "group_id" in members_df.columns:
                g_members = members_df[members_df["group_id"].astype(str) == group_id]
                if not g_members.empty:
                    if member_count == 0:
                        member_count = len(g_members)
                    if "role" in g_members.columns:
                        admin_count = int((g_members["role"] == "admin").sum())
                    for _, m_row in g_members.iterrows():
                        u_id = str(m_row["user_id"])
                        is_m = bool(m_row.get("is_muted", False))
                        mute_map[u_id] = is_m

            # 3. User Participation Map & Recent Activity
            recent_activity = 0
            user_part: dict[str, int] = {}
            if not history_df.empty and "contact_id" in history_df.columns:
                # Messages directed to or within group
                g_hist = history_df[history_df["contact_id"].astype(str) == group_id]
                recent_activity = len(g_hist)
                if not g_hist.empty and "user_id" in g_hist.columns:
                    for u_id, count in g_hist["user_id"].value_counts().items():
                        user_part[str(u_id)] = int(count)

            # 4. Activity Score & Importance Score Calculation
            activity_score = round(min(1.0, recent_activity / max(1, member_count * 5)), 4)

            # Base type weight
            type_weights = {
                "Announcements": 0.9,
                "Office": 0.85,
                "Family": 0.8,
                "School": 0.7,
                "Apartment": 0.6,
                "Sports": 0.5,
                "Community": 0.5,
                "Other": 0.4,
            }
            type_weight = type_weights.get(g_type, 0.4)
            importance_score = round(min(1.0, (type_weight * 0.5) + (activity_score * 0.3) + min(0.2, admin_count * 0.05)), 4)

            profile = GroupProfile(
                group_id=group_id,
                group_name=group_name,
                group_type=g_type,
                member_count=member_count,
                admin_count=admin_count,
                recent_activity=recent_activity,
                activity_score=activity_score,
                user_participation=user_part,
                mute_state=mute_map,
                importance_score=importance_score,
            )
            profiles[group_id] = profile

        self._cache = profiles
        logger.info(f"Built GroupProfile contexts for {len(profiles)} groups.")
        return profiles
