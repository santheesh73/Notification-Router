"""Unit tests for RuleRegistry."""

from src.rules.greeting_rule import GreetingRule
from src.rules.priority import RulePriority
from src.rules.rule_registry import RuleRegistry
from src.rules.scam_rule import ScamRule


def test_rule_registry_priority_ordering() -> None:
    """Test registry priority ordering (CRITICAL before LOW)."""
    registry = RuleRegistry()
    scam = ScamRule()
    greeting = GreetingRule()

    # Register in reverse order
    registry.register_rule(greeting)
    registry.register_rule(scam)

    active_rules = registry.get_active_rules()
    assert len(active_rules) == 2
    assert active_rules[0].name == "ScamRule"
    assert active_rules[1].name == "GreetingRule"


def test_rule_enable_disable() -> None:
    """Test enabling and disabling rules in registry."""
    registry = RuleRegistry()
    scam = ScamRule()
    registry.register_rule(scam)

    assert len(registry.get_active_rules()) == 1

    registry.disable_rule("ScamRule")
    assert len(registry.get_active_rules()) == 0

    registry.enable_rule("ScamRule")
    assert len(registry.get_active_rules()) == 1
