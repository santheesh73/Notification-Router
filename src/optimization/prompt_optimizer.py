"""Prompt Optimizer for Token & Context Efficiency."""

from dataclasses import asdict, dataclass
from typing import Any

from src.utils.logger import logger


@dataclass
class PromptOptimizationMetrics:
    """Dataclass holding prompt efficiency stats."""

    character_length: int = 0
    estimated_tokens: int = 0
    token_savings_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


class PromptOptimizer:
    """Optimizes LLM prompt token efficiency and context formatting."""

    def optimize_prompt_string(self, prompt: str) -> tuple[str, PromptOptimizationMetrics]:
        """Sanitize and optimize prompt string for token efficiency.

        Args:
            prompt: Raw input prompt string.

        Returns:
            Tuple of (compact_prompt_str, PromptOptimizationMetrics).
        """
        original_len = len(prompt)
        # Strip excessive blank lines or spaces
        compact_lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        compact_str = "\n".join(compact_lines)

        compact_len = len(compact_str)
        tokens = int(compact_len / 4.0)

        savings = round(((original_len - compact_len) / max(1, original_len)) * 100.0, 2)
        metrics = PromptOptimizationMetrics(
            character_length=compact_len,
            estimated_tokens=tokens,
            token_savings_percent=savings,
        )

        logger.debug(f"Prompt Optimizer: Compacted prompt from {original_len} to {compact_len} chars ({savings}% savings).")
        return compact_str, metrics
