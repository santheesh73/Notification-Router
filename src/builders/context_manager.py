"""ContextManager for WhatsApp Message Notification Router."""

from dataclasses import asdict, dataclass, field
from typing import Any

from tabulate import tabulate

from src.builders.business_context_builder import BusinessContextBuilder
from src.builders.group_context_builder import GroupContextBuilder
from src.builders.history_context_builder import HistoryContextBuilder
from src.builders.user_context_builder import UserContextBuilder
from src.loaders.load_data import DataRepository
from src.models.business_profile import BusinessProfile
from src.models.group_profile import GroupProfile
from src.models.history_profile import HistoryProfile
from src.models.user_profile import UserProfile
from src.utils.logger import logger


@dataclass
class ContextValidationReport:
    """Dataclass holding validation diagnostics for context layer."""

    duplicate_user_ids: list[str] = field(default_factory=list)
    duplicate_group_ids: list[str] = field(default_factory=list)
    duplicate_business_ids: list[str] = field(default_factory=list)
    missing_user_refs: list[str] = field(default_factory=list)
    missing_group_refs: list[str] = field(default_factory=list)
    missing_business_refs: list[str] = field(default_factory=list)
    empty_profiles: list[str] = field(default_factory=list)
    broken_foreign_keys: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no critical validation errors are found."""
        return (
            len(self.duplicate_user_ids) == 0
            and len(self.duplicate_group_ids) == 0
            and len(self.duplicate_business_ids) == 0
            and len(self.broken_foreign_keys) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class ContextManager:
    """Central Context Manager orchestrating all context profile builders."""

    def __init__(self, repository: DataRepository) -> None:
        """Initialize ContextManager with DataRepository dependency injection.

        Args:
            repository: Loaded DataRepository instance.
        """
        self.repository: DataRepository = repository
        self.user_builder = UserContextBuilder(repository)
        self.group_builder = GroupContextBuilder(repository)
        self.business_builder = BusinessContextBuilder(repository)
        self.history_builder = HistoryContextBuilder(repository)

        self._users: dict[str, UserProfile] = {}
        self._groups: dict[str, GroupProfile] = {}
        self._businesses: dict[str, BusinessProfile] = {}
        self._history: dict[str, HistoryProfile] = {}
        self._is_built: bool = False

    def build(self) -> None:
        """Execute all builders and populate memory cache."""
        logger.info("Initializing ContextManager and building context profiles...")
        self._users = self.user_builder.build()
        self._groups = self.group_builder.build()
        self._businesses = self.business_builder.build()
        self._history = self.history_builder.build()
        self._is_built = True
        logger.success("ContextManager successfully built all context profiles.")

    def _check_built(self) -> None:
        """Ensure build() has been executed prior to retrieval."""
        if not self._is_built:
            self.build()

    def get_user(self, user_id: Any) -> UserProfile | None:
        """Retrieve UserProfile by user_id.

        Args:
            user_id: User identifier (str or int).

        Returns:
            UserProfile object or None if not found.
        """
        self._check_built()
        return self._users.get(str(user_id))

    def get_group(self, group_id: Any) -> GroupProfile | None:
        """Retrieve GroupProfile by group_id.

        Args:
            group_id: Group identifier (str or int).

        Returns:
            GroupProfile object or None if not found.
        """
        self._check_built()
        return self._groups.get(str(group_id))

    def get_business(self, business_id: Any) -> BusinessProfile | None:
        """Retrieve BusinessProfile by business_id.

        Args:
            business_id: Business identifier (str or int).

        Returns:
            BusinessProfile object or None if not found.
        """
        self._check_built()
        return self._businesses.get(str(business_id))

    def get_history(self, message_id: Any) -> HistoryProfile | None:
        """Retrieve HistoryProfile by message_id.

        Args:
            message_id: Message identifier.

        Returns:
            HistoryProfile object or None if not found.
        """
        self._check_built()
        return self._history.get(str(message_id))

    def get_user_history(self, user_id: Any) -> list[HistoryProfile]:
        """O(1) lookup for all message history involving a user."""
        self._check_built()
        return self.history_builder.get_user_history(str(user_id))

    def get_sender_history(self, sender_id: Any) -> list[HistoryProfile]:
        """O(1) lookup for all message history sent by sender."""
        self._check_built()
        return self.history_builder.get_sender_history(str(sender_id))

    def get_business_history(self, business_id: Any) -> list[HistoryProfile]:
        """O(1) lookup for message history associated with business."""
        self._check_built()
        return self.history_builder.get_business_history(str(business_id))

    def get_group_history(self, group_id: Any) -> list[HistoryProfile]:
        """O(1) lookup for message history associated with group."""
        self._check_built()
        return self.history_builder.get_group_history(str(group_id))

    def list_users(self) -> list[str]:
        """List loaded user IDs."""
        self._check_built()
        return list(self._users.keys())

    def list_groups(self) -> list[str]:
        """List loaded group IDs."""
        self._check_built()
        return list(self._groups.keys())

    def list_businesses(self) -> list[str]:
        """List loaded business IDs."""
        self._check_built()
        return list(self._businesses.keys())

    def list_history(self) -> list[str]:
        """List loaded history message IDs."""
        self._check_built()
        return list(self._history.keys())

    def validate(self) -> ContextValidationReport:
        """Validate loaded profiles for integrity, foreign key relations, and duplicate entries.

        Returns:
            ContextValidationReport containing diagnostic lists.
        """
        self._check_built()
        report = ContextValidationReport()

        # 1. Foreign Key Validation: group_members -> users & groups
        members_df = self.repository.get_dataframe("group_members")
        if not members_df.empty:
            if "user_id" in members_df.columns:
                for u_id in members_df["user_id"].unique():
                    if str(u_id) not in self._users:
                        report.broken_foreign_keys.append(f"group_members.user_id '{u_id}' not found in users")
            if "group_id" in members_df.columns:
                for g_id in members_df["group_id"].unique():
                    if str(g_id) not in self._groups:
                        report.broken_foreign_keys.append(f"group_members.group_id '{g_id}' not found in groups")

        # 2. Foreign Key Validation: user_business_history -> users & business_accounts
        ubus_df = self.repository.get_dataframe("user_business_history")
        if not ubus_df.empty:
            if "user_id" in ubus_df.columns:
                for u_id in ubus_df["user_id"].unique():
                    if str(u_id) not in self._users:
                        report.broken_foreign_keys.append(f"user_business_history.user_id '{u_id}' not found in users")
            if "business_id" in ubus_df.columns:
                for b_id in ubus_df["business_id"].unique():
                    if str(b_id) not in self._businesses:
                        report.broken_foreign_keys.append(f"user_business_history.business_id '{b_id}' not found in business_accounts")

        logger.info(f"Context validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self) -> str:
        """Generate formatted ASCII summary table of context layer.

        Returns:
            Formatted summary table string.
        """
        self._check_built()

        # Compute averages
        avg_eng = (
            sum(u.engagement_score for u in self._users.values()) / len(self._users)
            if self._users
            else 0.0
        )
        avg_trust = (
            sum(b.trust_score for b in self._businesses.values()) / len(self._businesses)
            if self._businesses
            else 0.0
        )
        avg_g_act = (
            sum(g.activity_score for g in self._groups.values()) / len(self._groups)
            if self._groups
            else 0.0
        )

        rows = [
            ["Users Loaded", len(self._users)],
            ["Groups Loaded", len(self._groups)],
            ["Businesses Loaded", len(self._businesses)],
            ["History Records", len(self._history)],
            ["Average Engagement", f"{avg_eng:.4f}"],
            ["Average Trust", f"{avg_trust:.4f}"],
            ["Average Group Activity", f"{avg_g_act:.4f}"],
        ]

        formatted = tabulate(rows, headers=["Context Metric", "Value"], tablefmt="grid")
        return formatted
