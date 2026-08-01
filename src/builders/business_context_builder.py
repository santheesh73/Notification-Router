"""Business Context Profile Builder."""

from src.builders.base_builder import BaseContextBuilder
from src.models.business_profile import BusinessProfile
from src.utils.logger import logger


class BusinessContextBuilder(BaseContextBuilder[BusinessProfile]):
    """Builder for assembling BusinessProfile contexts from datasets."""

    def build(self) -> dict[str, BusinessProfile]:
        """Build BusinessProfile for every business in the repository.

        Returns:
            Dictionary mapping business_id -> BusinessProfile.
        """
        biz_df = self.get_dataset("business_accounts")
        ubus_df = self.get_dataset("user_business_history")
        hist_df = self.get_dataset("message_history")
        evts_df = self.get_dataset("message_events")

        if biz_df.empty:
            logger.warning("No business records found in repository.")
            return {}

        profiles: dict[str, BusinessProfile] = {}

        for _, row in biz_df.iterrows():
            biz_id = str(row["business_id"])
            brand_name = str(row.get("business_name", f"Business_{biz_id}"))
            verified = bool(row.get("verified", False))
            rating = float(row.get("rating", 4.0))

            # 1. Total Interactions & History Summary
            interaction_count = 0
            if not ubus_df.empty and "business_id" in ubus_df.columns:
                b_hist = ubus_df[ubus_df["business_id"].astype(str) == biz_id]
                if not b_hist.empty and "interaction_count" in b_hist.columns:
                    interaction_count = int(b_hist["interaction_count"].sum())

            if interaction_count == 0 and not hist_df.empty and "contact_id" in hist_df.columns:
                b_msg = hist_df[hist_df["contact_id"].astype(str) == biz_id]
                interaction_count = len(b_msg)

            # 2. Transaction Event Metrics (Orders, Payments, Bookings, Subscriptions, Reports)
            orders = 0
            payments = 0
            bookings = 0
            subscriptions = 0
            reports = 0
            opt_in = True
            opt_out = False

            # Infer from Category / History if present
            category = str(row.get("category", "")).lower()
            if "logistics" in category or "retail" in category:
                orders = max(1, interaction_count // 2)
            elif "finance" in category or "bank" in category:
                payments = max(1, interaction_count // 2)
            elif "hospitality" in category or "food" in category:
                bookings = max(1, interaction_count // 3)

            if not evts_df.empty and "user_action" in evts_df.columns:
                # Count reports if any
                reports = int((evts_df["user_action"] == "reported").sum())

            # 3. Calculate Trust Score
            # Verified bonus + Rating bonus + Interaction bonus - Report penalty
            verif_bonus = 0.4 if verified else 0.1
            rating_score = round(min(1.0, max(0.0, rating / 5.0)), 2) * 0.4
            interact_bonus = min(0.2, interaction_count * 0.01)
            report_penalty = min(0.3, reports * 0.1)

            trust_score = round(min(1.0, max(0.0, verif_bonus + rating_score + interact_bonus - report_penalty)), 4)

            profile = BusinessProfile(
                business_id=biz_id,
                brand_name=brand_name,
                verified=verified,
                account_age=365,  # Default 1 year account age
                reports=reports,
                orders=orders,
                payments=payments,
                bookings=bookings,
                subscriptions=subscriptions,
                opt_in=opt_in,
                opt_out=opt_out,
                interaction_count=interaction_count,
                trust_score=trust_score,
            )
            profiles[biz_id] = profile

        self._cache = profiles
        logger.info(f"Built BusinessProfile contexts for {len(profiles)} businesses.")
        return profiles
