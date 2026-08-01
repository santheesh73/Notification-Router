"""Temporal Feature Extractor."""

from datetime import datetime
from typing import Any

import pandas as pd

from src.builders.context_manager import ContextManager
from src.features.base_feature import BaseFeatureExtractor


class TemporalFeatureExtractor(BaseFeatureExtractor):
    """Extracts date, time, and schedule-relative temporal features."""

    def extract(
        self,
        message: dict[str, Any],
        context: ContextManager,
    ) -> dict[str, Any]:
        """Extract temporal features.

        Args:
            message: Message record dictionary.
            context: ContextManager instance.

        Returns:
            Dictionary of temporal feature signals.
        """
        raw_ts = message.get("timestamp")
        dt: datetime | None = None

        if raw_ts and pd.notnull(raw_ts):
            try:
                dt = pd.to_datetime(raw_ts).to_pydatetime()
            except Exception:
                dt = datetime.now()
        else:
            dt = datetime.now()

        hour = dt.hour
        day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
        weekend = day_of_week in [5, 6]
        night = hour >= 22 or hour < 6
        working_hours = (9 <= hour < 17) and not weekend

        # Quiet hours check from UserProfile
        user_id = str(message.get("recipient_id", message.get("user_id", "")))
        during_quiet_hours = False
        user_profile = context.get_user(user_id)

        if user_profile and user_profile.quiet_hours_start and user_profile.quiet_hours_end:
            try:
                q_start = int(user_profile.quiet_hours_start.split(":")[0])
                q_end = int(user_profile.quiet_hours_end.split(":")[0])
                if q_start <= q_end:
                    during_quiet_hours = q_start <= hour < q_end
                else:
                    during_quiet_hours = hour >= q_start or hour < q_end
            except Exception:
                during_quiet_hours = False
        else:
            during_quiet_hours = night

        return {
            "hour_of_day": hour,
            "day_of_week": day_of_week,
            "weekend": weekend,
            "night": night,
            "during_quiet_hours": during_quiet_hours,
            "working_hours": working_hours,
            "holiday_flag": False,
        }
