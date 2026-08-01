"""History Context Profile Builder with O(1) Index Lookups."""

from collections import defaultdict

from src.builders.base_builder import BaseContextBuilder
from src.models.history_profile import HistoryProfile
from src.utils.logger import logger


class HistoryContextBuilder(BaseContextBuilder[HistoryProfile]):
    """Builder for assembling HistoryProfile records and secondary O(1) indices."""

    def __init__(self, repository) -> None:
        super().__init__(repository)
        self._user_index: dict[str, list[HistoryProfile]] = defaultdict(list)
        self._sender_index: dict[str, list[HistoryProfile]] = defaultdict(list)
        self._business_index: dict[str, list[HistoryProfile]] = defaultdict(list)
        self._group_index: dict[str, list[HistoryProfile]] = defaultdict(list)

    def build(self) -> dict[str, HistoryProfile]:
        """Build HistoryProfile dictionary indexed by message_id with O(1) indices.

        Returns:
            Dictionary mapping message_id -> HistoryProfile.
        """
        msgs_df = self.get_dataset("messages")
        if msgs_df.empty:
            msgs_df = self.get_dataset("sample_messages")

        evts_df = self.get_dataset("message_events")
        mhist_df = self.get_dataset("message_history")

        profiles: dict[str, HistoryProfile] = {}
        self._user_index.clear()
        self._sender_index.clear()
        self._business_index.clear()
        self._group_index.clear()

        # 1. Map events per message_id if available
        events_map: dict[str, dict[str, bool]] = defaultdict(lambda: {"opened": False, "replied": False, "dismissed": False, "reported": False})
        event_time_map: dict[str, str] = {}

        if not evts_df.empty and "message_id" in evts_df.columns:
            for _, row in evts_df.iterrows():
                msg_id = str(row["message_id"])
                action = str(row.get("user_action", "")).lower()
                if action == "opened":
                    events_map[msg_id]["opened"] = True
                elif action == "replied":
                    events_map[msg_id]["replied"] = True
                elif action == "dismissed":
                    events_map[msg_id]["dismissed"] = True
                elif action == "reported":
                    events_map[msg_id]["reported"] = True

                if "event_timestamp" in row and row["event_timestamp"]:
                    event_time_map[msg_id] = str(row["event_timestamp"])

        # 2. Iterate through message_history dataset first (primary historical repository)
        if not mhist_df.empty:
            for _, row in mhist_df.iterrows():
                msg_id = str(row.get("message_id", row.get("history_id", "")))
                if not msg_id or msg_id == "nan":
                    continue

                recipient = str(row.get("user_id", "unknown"))
                sender_user = str(row.get("sender_user_id", ""))
                if sender_user == "nan": sender_user = ""

                grp_id = str(row.get("group_id", "")) if str(row.get("group_id", "")) not in ("nan", "") else None
                biz_id = str(row.get("business_id", "")) if str(row.get("business_id", "")) not in ("nan", "") else None

                sender = biz_id or sender_user or recipient
                conv_type = str(row.get("conversation_type", "direct"))
                m_text = str(row.get("message_text", "")) if str(row.get("message_text", "")) != "nan" else ""
                m_type = str(row.get("media_type", "")) if str(row.get("media_type", "")) != "nan" else None
                event_time = str(row.get("created_at", "")) or event_time_map.get(msg_id)

                evt_flags = events_map[msg_id]

                profile = HistoryProfile(
                    message_id=msg_id,
                    user_id=recipient,
                    sender=sender,
                    conversation=f"{conv_type}:{sender}",
                    group_id=grp_id,
                    business_id=biz_id,
                    message_text=m_text,
                    media_type=m_type,
                    opened=evt_flags["opened"],
                    replied=evt_flags["replied"],
                    dismissed=evt_flags["dismissed"],
                    reported=evt_flags["reported"],
                    event_time=event_time,
                )

                profiles[msg_id] = profile
                self._user_index[recipient].append(profile)
                if sender and sender != "unknown":
                    self._sender_index[sender].append(profile)
                if sender_user:
                    self._sender_index[sender_user].append(profile)
                if biz_id:
                    self._business_index[biz_id].append(profile)
                if grp_id:
                    self._group_index[grp_id].append(profile)

        # 3. Add current messages DataFrame to profiles if not already present
        if not msgs_df.empty:
            for _, row in msgs_df.iterrows():
                msg_id = str(row["message_id"])
                if msg_id not in profiles:
                    sender = str(row.get("sender_id", row.get("sender_user_id", "unknown")))
                    recipient = str(row.get("recipient_id", row.get("user_id", "unknown")))
                    grp_id = str(row.get("group_id", "")) if str(row.get("group_id", "")) not in ("nan", "") else None
                    biz_id = str(row.get("business_id", "")) if str(row.get("business_id", "")) not in ("nan", "") else None
                    m_text = str(row.get("message_text", "")) if str(row.get("message_text", "")) != "nan" else ""
                    m_type = str(row.get("media_type", "")) if str(row.get("media_type", "")) != "nan" else None
                    event_time = str(row.get("timestamp", "")) or event_time_map.get(msg_id)

                    conv = f"group:{grp_id}" if grp_id else (f"business:{biz_id}" if biz_id else f"direct:{sender}")
                    evt_flags = events_map[msg_id]

                    profile = HistoryProfile(
                        message_id=msg_id,
                        user_id=recipient,
                        sender=sender,
                        conversation=conv,
                        group_id=grp_id,
                        business_id=biz_id,
                        message_text=m_text,
                        media_type=m_type,
                        opened=evt_flags["opened"],
                        replied=evt_flags["replied"],
                        dismissed=evt_flags["dismissed"],
                        reported=evt_flags["reported"],
                        event_time=event_time,
                    )
                    profiles[msg_id] = profile
                    self._user_index[recipient].append(profile)
                    if sender and sender != "unknown":
                        self._sender_index[sender].append(profile)
                    if biz_id:
                        self._business_index[biz_id].append(profile)
                    if grp_id:
                        self._group_index[grp_id].append(profile)

        self._cache = profiles
        logger.info(f"Built HistoryProfile contexts for {len(profiles)} records.")
        return profiles

    def get_history_by_message(self, message_id: str) -> HistoryProfile | None:
        """O(1) lookup for history profile by message_id."""
        return self._cache.get(message_id)

    def get_user_history(self, user_id: str) -> list[HistoryProfile]:
        """O(1) lookup for history records related to a user_id."""
        return self._user_index.get(user_id, [])

    def get_sender_history(self, sender_id: str) -> list[HistoryProfile]:
        """O(1) lookup for history records sent by sender_id."""
        return self._sender_index.get(sender_id, [])

    def get_business_history(self, business_id: str) -> list[HistoryProfile]:
        """O(1) lookup for history records associated with business_id."""
        return self._business_index.get(business_id, [])

    def get_group_history(self, group_id: str) -> list[HistoryProfile]:
        """O(1) lookup for history records associated with group_id."""
        return self._group_index.get(group_id, [])
