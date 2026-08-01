"""Abstract Base Rule."""

from abc import ABC, abstractmethod

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.rules.priority import RulePriority
from src.rules.rule_result import RuleResult


class BaseRule(ABC):
    """Abstract base class for all deterministic notification routing rules."""

    def __init__(self, name: str, priority: RulePriority, enabled: bool = True) -> None:
        """Initialize BaseRule.

        Args:
            name: Human-readable name of the rule.
            priority: RulePriority level.
            enabled: Boolean flag indicating if rule is active.
        """
        self.name: str = name
        self.priority: RulePriority = priority
        self.enabled: bool = enabled

    @abstractmethod
    def evaluate(
        self,
        vector: FeatureVector,
        context: ContextManager,
    ) -> RuleResult | None:
        """Evaluate FeatureVector against rule conditions.

        Args:
            vector: Extracted FeatureVector instance.
            context: ContextManager instance.

        Returns:
            RuleResult if rule triggers, or None if conditions are not met.
        """
        pass
