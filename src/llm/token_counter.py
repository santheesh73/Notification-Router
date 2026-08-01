"""Token Counter and Usage Estimator."""


class TokenCounter:
    """Tracks token usage and calculates estimated cost metrics."""

    def __init__(self, cost_per_1k_tokens: float = 0.0015) -> None:
        """Initialize TokenCounter.

        Args:
            cost_per_1k_tokens: Cost float per 1,000 tokens (default $0.0015).
        """
        self.cost_per_1k: float = cost_per_1k_tokens
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for input text string.

        Args:
            text: Text string.

        Returns:
            Token count integer.
        """
        if not text:
            return 0
        words = text.split()
        return max(1, int(len(words) * 1.3))

    def record_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage.

        Args:
            prompt_tokens: Number of prompt input tokens.
            completion_tokens: Number of completion output tokens.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    @property
    def total_tokens(self) -> int:
        """Get total cumulative tokens."""
        return self.total_prompt_tokens + self.total_completion_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Calculate estimated total cost in USD."""
        return round((self.total_tokens / 1000.0) * self.cost_per_1k, 6)
