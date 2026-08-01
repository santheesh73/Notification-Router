"""Retry Handler for resilient LLM inference."""

from typing import Any

from src.llm.llm_provider import LLMProvider
from src.llm.response_parser import ResponseParser
from src.llm.response_validator import ResponseValidator
from src.utils.logger import logger


class RetryHandler:
    """Manages LLM retries for invalid responses with deterministic fallback."""

    def __init__(self, max_retries: int = 3) -> None:
        """Initialize RetryHandler.

        Args:
            max_retries: Maximum number of generation attempts (default 3).
        """
        self.max_retries: int = max_retries
        self.parser: ResponseParser = ResponseParser()
        self.validator: ResponseValidator = ResponseValidator()

    def execute_with_retry(
        self,
        provider: LLMProvider,
        prompt: str,
    ) -> tuple[dict[str, Any], int]:
        """Execute LLM generation with retry logic.

        Args:
            provider: Concrete LLMProvider instance.
            prompt: Text prompt string.

        Returns:
            Tuple of (validated_response_dict, total_attempts_made).
        """
        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                raw_text = provider.generate(prompt)
                parsed = self.parser.parse(raw_text)
                is_valid, err_msg = self.validator.validate(parsed)

                if is_valid:
                    return parsed, attempt

                last_error = err_msg
                logger.warning(f"LLM attempt {attempt}/{self.max_retries} failed validation: {err_msg}")
            except Exception as exc:
                last_error = str(exc)
                logger.error(f"LLM attempt {attempt}/{self.max_retries} encountered error: {exc}")

        logger.warning(f"All {self.max_retries} LLM attempts failed ({last_error}). Triggering safe fallback.")
        fallback = {
            "action": "digest",
            "message_type": "unknown",
            "reason": "Unable to confidently classify.",
            "confidence": 0.50,
        }
        return fallback, self.max_retries
