"""Rule Registry for managing and ordering notification rules."""

from src.rules.base_rule import BaseRule
from src.utils.logger import logger


class RuleRegistry:
    """Registry maintaining registered notification routing rules and priority ordering."""

    def __init__(self) -> None:
        """Initialize empty RuleRegistry."""
        self._rules: dict[str, BaseRule] = {}

    def register_rule(self, rule: BaseRule) -> None:
        """Register a notification routing rule.

        Args:
            rule: BaseRule subclass instance.
        """
        self._rules[rule.name] = rule
        logger.debug(f"Registered rule '{rule.name}' with priority {rule.priority}.")

    def enable_rule(self, rule_name: str) -> None:
        """Enable a registered rule by name.

        Args:
            rule_name: Name of rule to enable.
        """
        if rule_name in self._rules:
            self._rules[rule_name].enabled = True
            logger.info(f"Enabled rule '{rule_name}'.")

    def disable_rule(self, rule_name: str) -> None:
        """Disable a registered rule by name.

        Args:
            rule_name: Name of rule to disable.
        """
        if rule_name in self._rules:
            self._rules[rule_name].enabled = False
            logger.info(f"Disabled rule '{rule_name}'.")

    def get_all_rules(self) -> list[BaseRule]:
        """Get all registered rules sorted by priority level.

        Returns:
            List of BaseRule instances sorted by priority (CRITICAL -> LOW).
        """
        return sorted(self._rules.values(), key=lambda r: int(r.priority))

    def get_active_rules(self) -> list[BaseRule]:
        """Get all currently enabled rules sorted by priority level.

        Returns:
            List of active BaseRule instances sorted by priority (CRITICAL -> LOW).
        """
        active = [r for r in self._rules.values() if r.enabled]
        return sorted(active, key=lambda r: int(r.priority))
