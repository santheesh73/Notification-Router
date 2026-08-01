"""User Context Profile Builder."""

import pandas as pd

from src.builders.base_builder import BaseContextBuilder
from src.models.user_profile import UserProfile
from src.utils.logger import logger


class UserContextBuilder(BaseContextBuilder[UserProfile]):
    """Builder for assembling UserProfile contexts from datasets."""

    def build(self) -> dict[str, UserProfile]:
        """Build UserProfile for every user in the repository.

        Returns:
            Dictionary mapping user_id -> UserProfile.
        """
        users_df = self.get_dataset("users")
        members_df = self.get_dataset("group_members")
        events_df = self.get_dataset("message_events")
        summary_df = self.get_dataset("daily_notification_summary")
        business_hist_df = self.get_dataset("user_business_history")
        message_hist_df = self.get_dataset("message_history")

        if users_df.empty:
            logger.warning("No user records found in repository.")
            return {}

        profiles: dict[str, UserProfile] = {}

        for _, row in users_df.iterrows():
            user_id = str(row["user_id"])

            # 1. Parse quiet hours / preferences if available
            quiet_start = str(row.get("quiet_hours_start", "")) if pd.notnull(row.get("quiet_hours_start")) else None
            quiet_end = str(row.get("quiet_hours_end", "")) if pd.notnull(row.get("quiet_hours_end")) else None

            # 2. Extract muted groups for this user
            muted_groups: list[str] = []
            if not members_df.empty and "user_id" in members_df.columns:
                user_m = members_df[members_df["user_id"].astype(str) == user_id]
                if "is_muted" in user_m.columns:
                    muted_rows = user_m[user_m["is_muted"] == True]  # noqa: E712
                    muted_groups = [str(g) for g in muted_rows["group_id"].unique()]

            # 3. Calculate event telemetry (opens, replies, dismissals, reports)
            opens = 0
            replies = 0
            dismissals = 0
            reports = 0
            last_active = None

            if not events_df.empty and "message_id" in events_df.columns:
                # Filter events where user carried out an action or events relevant to user
                if "user_action" in events_df.columns:
                    user_evts = events_df
                    opens = int((user_evts["user_action"] == "opened").sum())
                    replies = int((user_evts["user_action"] == "replied").sum())
                    dismissals = int((user_evts["user_action"] == "dismissed").sum())
                    reports = int((user_evts["user_action"] == "reported").sum())

                if "event_timestamp" in events_df.columns and not events_df["event_timestamp"].empty:
                    last_active = str(events_df["event_timestamp"].max())

            # 4. Calculate daily notification load
            notif_load = 0.0
            if not summary_df.empty and "user_id" in summary_df.columns:
                u_sum = summary_df[summary_df["user_id"].astype(str) == user_id]
                if not u_sum.empty and "total_received" in u_sum.columns:
                    notif_load = float(u_sum["total_received"].mean())

            # 5. Extract trusted/favorite businesses
            trusted_businesses: list[str] = []
            favorite_businesses: list[str] = []
            if not business_hist_df.empty and "user_id" in business_hist_df.columns:
                u_bus = business_hist_df[business_hist_df["user_id"].astype(str) == user_id]
                if not u_bus.empty and "interaction_count" in u_bus.columns:
                    sorted_bus = u_bus.sort_values(by="interaction_count", ascending=False)
                    favorite_businesses = [str(b) for b in sorted_bus["business_id"].unique()]
                    trusted_rows = u_bus[u_bus["interaction_count"] >= 5]
                    trusted_businesses = [str(b) for b in trusted_rows["business_id"].unique()]

            # 6. Extract trusted contacts & favorite groups
            trusted_contacts: list[str] = []
            favorite_groups: list[str] = []
            if not message_hist_df.empty and "user_id" in message_hist_df.columns:
                u_hist = message_hist_df[message_hist_df["user_id"].astype(str) == user_id]
                if not u_hist.empty and "contact_id" in u_hist.columns:
                    trusted_contacts = [str(c) for c in u_hist["contact_id"].dropna().unique() if str(c).startswith("USR")]
                if not members_df.empty and "user_id" in members_df.columns:
                    u_grps = members_df[members_df["user_id"].astype(str) == user_id]
                    favorite_groups = [str(g) for g in u_grps["group_id"].unique()]

            # 7. Calculate rates & engagement score
            total_events = max(1, opens + replies + dismissals + reports)
            open_rate = round(opens / total_events, 4)
            reply_rate = round(replies / total_events, 4)
            dismiss_rate = round(dismissals / total_events, 4)
            report_rate = round(reports / total_events, 4)

            # Engagement score formula
            engagement_score = round(min(1.0, max(0.0, (open_rate * 0.5) + (reply_rate * 0.5) - (dismiss_rate * 0.2))), 4)

            profile = UserProfile(
                user_id=user_id,
                quiet_hours_start=quiet_start,
                quiet_hours_end=quiet_end,
                opens=opens,
                replies=replies,
                dismissals=dismissals,
                reports=reports,
                notification_load=notif_load,
                trusted_contacts=trusted_contacts,
                trusted_businesses=trusted_businesses,
                muted_groups=muted_groups,
                reply_rate=reply_rate,
                open_rate=open_rate,
                dismiss_rate=dismiss_rate,
                report_rate=report_rate,
                engagement_score=engagement_score,
                last_active=last_active,
                favorite_groups=favorite_groups,
                favorite_businesses=favorite_businesses,
            )
            profiles[user_id] = profile

        self._cache = profiles
        logger.info(f"Built UserProfile contexts for {len(profiles)} users.")
        return profiles
