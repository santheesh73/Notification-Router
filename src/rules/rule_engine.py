"""Notification Rule Engine."""

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.business_rule import BusinessRule
from src.rules.duplicate_rule import DuplicateRule
from src.rules.event_rule import EventRule
from src.rules.family_rule import FamilyRule
from src.rules.forward_rule import ForwardRule
from src.rules.greeting_rule import GreetingRule
from src.rules.muted_group_rule import MutedGroupRule
from src.rules.office_rule import OfficeRule
from src.rules.payment_rule import PaymentRule
from src.rules.personal_rule import PersonalRule
from src.rules.promotion_rule import PromotionRule
from src.rules.reminder_rule import ReminderRule
from src.rules.rule_registry import RuleRegistry
from src.rules.rule_result import RuleResult
from src.rules.scam_rule import ScamRule
from src.rules.spam_rule import SpamRule
from src.rules.urgent_rule import UrgentRule
from src.utils.logger import logger


class NotificationRuleEngine:
    """Primary deterministic rule engine for classifying WhatsApp message notifications."""

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        """Initialize NotificationRuleEngine and register default rules.

        Args:
            registry: Optional custom RuleRegistry instance.
        """
        self.registry: RuleRegistry = registry or RuleRegistry()

        if registry is None:
            self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register all 15 deterministic rules into registry."""
        default_rules = [
            ScamRule(),
            UrgentRule(),
            SpamRule(),
            PaymentRule(),
            MutedGroupRule(),
            DuplicateRule(),
            FamilyRule(),
            OfficeRule(),
            BusinessRule(),
            ReminderRule(),
            EventRule(),
            PersonalRule(),
            ForwardRule(),
            PromotionRule(),
            GreetingRule(),
        ]
        for rule in default_rules:
            self.registry.register_rule(rule)
        logger.info(f"NotificationRuleEngine registered {len(default_rules)} default rules.")

    def route(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult:
        """Route a single message FeatureVector through active rules by priority order.

        Args:
            vector: Extracted FeatureVector instance.
            context: ContextManager instance.

        Returns:
            RuleResult instance (resolved or unresolved).
        """
        active_rules = self.registry.get_active_rules()

        for rule in active_rules:
            result = rule.evaluate(vector, context)
            if result is not None and result.resolved:
                logger.debug(f"Message '{vector.message_id}' resolved by '{rule.name}' -> {result.action}")
                return result

        # Fallback if no deterministic rule matches
        logger.debug(f"Message '{vector.message_id}' unresolved by Rule Engine. Routing to AI.")
        return RuleResult(
            message_id=vector.message_id,
            resolved=False,
            action="unresolved",
            message_type="general",
            reason="No deterministic rule matched. Requires AI reasoning.",
            confidence=0.0,
            triggered_rule="None",
            priority="LOW",
            requires_ai=True,
        )
