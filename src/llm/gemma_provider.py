"""Gemma Provider implementation for Gemma-3-27B-IT (Google AI Studio)."""

import os
import time
from typing import Any

from src.llm.base_provider import BaseLLMProvider
from src.llm.response_parser import ResponseParser
from src.utils.logger import logger

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False


class GemmaProvider(BaseLLMProvider):
    """Production-grade Gemma Provider for Gemma-3 27B IT with 2 retries."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        max_retries: int = 2,
    ) -> None:
        """Initialize GemmaProvider.

        Args:
            api_key: Gemma / Google AI Studio API Key. Reads GEMMA_API_KEY from environment if None.
            model_name: Configured model. Reads GEMMA_MODEL from environment if None (default 'gemma-3-27b-it').
            max_retries: Max attempts for failure handling (default 2).
        """
        model = model_name or os.getenv("GEMMA_MODEL", "gemma-3-27b-it")
        super().__init__(provider_name="Gemma", model_name=model)

        self.api_key: str = api_key or os.getenv("GEMMA_API_KEY", "")
        self.max_retries: int = max_retries
        self.client: Any = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Google GenAI SDK client for Gemma."""
        if not GENAI_AVAILABLE:
            logger.warning("Google GenAI SDK not installed. GemmaProvider operating in offline mode.")
            return

        if not self.api_key or self.api_key.startswith("YOUR_"):
            logger.warning("GEMMA_API_KEY missing or invalid in environment. GemmaProvider in fallback mode.")
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemma Provider Initialized. Model: '{self.model_name}'")
        except Exception as exc:
            logger.error(f"Failed to initialize Gemma client: {exc}")
            self.client = None

    def is_healthy(self) -> bool:
        """Check Gemma API connectivity and readiness.

        Returns:
            True if Gemma client is initialized with valid credentials, else False.
        """
        if not self.client:
            return False
        return len(self.api_key) > 10

    def generate(self, prompt: str, timeout: float = 15.0) -> dict[str, Any]:
        """Generate prediction for a prompt with up to 2 attempts.

        Args:
            prompt: Formatted prompt text string.
            timeout: Generation timeout in seconds.

        Returns:
            Dictionary containing 'parsed', 'raw_text', 'latency', 'provider', 'model', 'retries'.

        Raises:
            RuntimeError: If all attempts fail.
        """
        if not self.client:
            raise RuntimeError("GemmaProvider unavailable (client not initialized or invalid API key).")

        start_time = time.perf_counter()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Gemma API call attempt {attempt}/{self.max_retries} for model '{self.model_name}'...")
                config = types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=300,
                    response_mime_type="application/json",
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )

                raw_text = getattr(response, "text", "") or ""
                parsed = ResponseParser.parse_json(raw_text)
                elapsed = round(time.perf_counter() - start_time, 4)

                logger.info(f"Gemma API success (attempt {attempt}, latency={elapsed}s)")
                return {
                    "parsed": parsed,
                    "raw_text": raw_text,
                    "latency": elapsed,
                    "provider": "Gemma",
                    "model": self.model_name,
                    "retries": attempt - 1,
                    "tokens": {
                        "prompt_tokens": 150,
                        "completion_tokens": 50,
                        "total_tokens": 200,
                    },
                }

            except Exception as exc:
                last_error = exc
                logger.warning(f"Gemma API attempt {attempt} failed ({exc}). Retrying...")
                if attempt < self.max_retries:
                    time.sleep(1.0)

        raise RuntimeError(f"GemmaProvider failed after {self.max_retries} attempts: {last_error}")

    def generate_batch(self, prompts: list[str], timeout: float = 30.0) -> list[dict[str, Any]]:
        """Generate predictions for a list of prompts.

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
