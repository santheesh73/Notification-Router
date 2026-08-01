"""Groq Provider implementation for Llama-3.3-70B-Versatile."""

import os
import time
from typing import Any

from src.llm.base_provider import BaseLLMProvider
from src.llm.response_parser import ResponseParser
from src.utils.logger import logger

try:
    from groq import Groq
    GROQ_SDK_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_SDK_AVAILABLE = False


class GroqProvider(BaseLLMProvider):
    """Production-grade Groq Provider for Llama-3.3 70B with 3 exponential backoff retries."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        max_retries: int = 3,
        base_backoff: float = 1.0,
    ) -> None:
        """Initialize GroqProvider.

        Args:
            api_key: Groq API Key. Reads GROQ_API_KEY from environment if None.
            model_name: Configured model. Reads GROQ_MODEL from environment if None (default 'llama-3.3-70b-versatile').
            max_retries: Max attempts for failure handling (default 3).
            base_backoff: Base exponential backoff delay in seconds (default 1.0).
        """
        model = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        super().__init__(provider_name="Groq", model_name=model)

        self.api_key: str = api_key or os.getenv("GROQ_API_KEY", "")
        self.max_retries: int = max_retries
        self.base_backoff: float = base_backoff
        self.client: Any = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Groq SDK client."""
        if not GROQ_SDK_AVAILABLE:
            logger.warning("Groq SDK ('groq' package) not installed. GroqProvider operating in offline fallback mode.")
            return

        if not self.api_key or self.api_key.startswith("YOUR_") or self.api_key.startswith("gsk_placeholder"):
            logger.warning("GROQ_API_KEY missing or invalid in environment. GroqProvider in fallback mode.")
            return

        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"Groq Provider Initialized. Model: '{self.model_name}'")
        except Exception as exc:
            logger.error(f"Failed to initialize Groq client: {exc}")
            self.client = None

    def is_healthy(self) -> bool:
        """Check Groq API connectivity and readiness.

        Returns:
            True if Groq client is initialized with valid credentials, else False.
        """
        if not self.client:
            return False
        # Quick validation check
        return len(self.api_key) > 10

    def generate(self, prompt: str, timeout: float = 15.0) -> dict[str, Any]:
        """Generate prediction for a single prompt with up to 3 retries and exponential backoff.

        Args:
            prompt: Formatted prompt text string.
            timeout: Generation timeout in seconds.

        Returns:
            Dictionary containing 'parsed', 'raw_text', 'latency', 'provider', 'model', 'retries'.

        Raises:
            RuntimeError: If all 3 attempts fail.
        """
        if not self.client:
            raise RuntimeError("GroqProvider unavailable (client not initialized or invalid API key).")

        start_time = time.perf_counter()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Groq API call attempt {attempt}/{self.max_retries} for model '{self.model_name}'...")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a precise JSON-only notification classifier."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=300,
                    response_format={"type": "json_object"},
                    timeout=timeout,
                )

                raw_text = response.choices[0].message.content or ""
                parsed = ResponseParser.parse_json(raw_text)
                elapsed = round(time.perf_counter() - start_time, 4)

                prompt_tokens = getattr(getattr(response, "usage", None), "prompt_tokens", 0)
                comp_tokens = getattr(getattr(response, "usage", None), "completion_tokens", 0)

                logger.info(f"Groq API success (attempt {attempt}, latency={elapsed}s)")
                return {
                    "parsed": parsed,
                    "raw_text": raw_text,
                    "latency": elapsed,
                    "provider": "Groq",
                    "model": self.model_name,
                    "retries": attempt - 1,
                    "tokens": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": comp_tokens,
                        "total_tokens": prompt_tokens + comp_tokens,
                    },
                }

            except Exception as exc:
                last_error = exc
                backoff = self.base_backoff * (2 ** (attempt - 1))
                logger.warning(f"Groq API attempt {attempt} failed ({exc}). Retrying in {backoff:.1f}s...")
                if attempt < self.max_retries:
                    time.sleep(backoff)

        raise RuntimeError(f"GroqProvider failed after {self.max_retries} attempts: {last_error}")

    def generate_batch(self, prompts: list[str], timeout: float = 30.0) -> list[dict[str, Any]]:
        """Generate predictions for a list of prompts sequentially or in batch.

        Args:
            prompts: List of prompt strings.
            timeout: Generation timeout per prompt.

        Returns:
            List of result dictionaries matching generate() format.
        """
        results = []
        for prompt in prompts:
            res = self.generate(prompt=prompt, timeout=timeout)
            results.append(res)
        return results
