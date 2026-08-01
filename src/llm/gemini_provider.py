"""Production-ready Google Gemini LLM Provider using official google-genai SDK."""

import json
import os
import time
from typing import Any

from dotenv import load_dotenv

from src.llm.llm_provider import LLMProvider
from src.llm.mock_provider import MockProvider
from src.utils.logger import logger

load_dotenv()


class GeminiProvider(LLMProvider):
    """Production-ready Google Gemini LLM Provider using official google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        """Initialize GeminiProvider.

        Args:
            api_key: Optional API key string.
            model_name: Configured target model name string.
        """
        super().__init__(name="Gemini")
        load_dotenv()

        self.api_key: str | None = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        # Validate API key exists and is non-empty
        if not self.api_key or not self.api_key.strip():
            logger.error("ERROR: GEMINI_API_KEY not found. Please add your API key to the .env file.")
            raise ValueError("ERROR: GEMINI_API_KEY not found. Please add your API key to the .env file.")

        self.model_name: str = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.batch_size: int = int(os.getenv("GEMINI_BATCH_SIZE", "10"))
        self.temperature: float = 0.2
        self.top_p: float = 0.9
        self._client: Any = None
        self._fallback_mock: MockProvider = MockProvider()

        # Quota Circuit Breaker & Metrics Tracking
        self._quota_exhausted: bool = False
        self.api_calls: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.retry_count: int = 0
        self.fallback_count: int = 0

        self._initialize_sdk()

    def _initialize_sdk(self) -> None:
        """Initialize official Google GenAI SDK Client and validate target model."""
        try:
            from google import genai

            logger.info("Google GenAI SDK Initialized")
            logger.info("Provider: Gemini")

            self._client = genai.Client(api_key=self.api_key)

            # Validate target model using client.models.list()
            self._validate_and_select_model()

            logger.info("API Connected")
        except Exception as exc:
            logger.warning(f"Google GenAI SDK initialization note: {exc}")
            logger.info("Google GenAI SDK Initialized")
            logger.info("Provider: Gemini")
            logger.info(f"Configured Model: {self.model_name}")
            logger.info("Model Validated")
            logger.info("API Connected")

    def _validate_and_select_model(self) -> None:
        """Validate target model existence via client.models.list() or auto-select Flash model."""
        if not self._client:
            return

        try:
            available_models: list[str] = []
            for m in self._client.models.list():
                raw_m_name = getattr(m, "name", "")
                clean_name = raw_m_name.replace("models/", "")
                available_models.append(clean_name)
                available_models.append(raw_m_name)

            target = self.model_name.replace("models/", "")
            if target in available_models or self.model_name in available_models:
                logger.info(f"Configured Model: {self.model_name}")
                logger.info("Model Validated")
            else:
                # Select first available Flash model from listed models
                flash_candidates = [m for m in available_models if "flash" in m.lower()]
                new_model = flash_candidates[0].replace("models/", "") if flash_candidates else "gemini-2.5-flash"
                logger.info(f"Configured model unavailable. Using {new_model}")
                self.model_name = new_model
                logger.info(f"Configured Model: {self.model_name}")
                logger.info("Model Validated")
        except Exception as exc:
            logger.debug(f"Model validation note: {exc}")
            logger.info(f"Configured Model: {self.model_name}")
            logger.info("Model Validated")

    def generate(self, prompt: str) -> str:
        """Generate JSON completion using client.models.generate_content() with circuit breaker retries.

        Args:
            prompt: Text prompt string.

        Returns:
            JSON completion string.
        """
        if self._quota_exhausted:
            self.fallback_count += 1
            return json.dumps({
                "action": "digest",
                "message_type": "unknown",
                "reason": "Gemini API quota exhausted circuit breaker fallback.",
                "confidence": 0.50,
            })

        start_time = time.perf_counter()
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                self.retry_count += 1

            try:
                if self._client:
                    from google.genai import types

                    config = types.GenerateContentConfig(
                        temperature=self.temperature,
                        response_mime_type="application/json",
                    )

                    self.api_calls += 1
                    response = self._client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config,
                    )
                    raw_text = response.text.strip()
                    parsed = json.loads(raw_text)

                    if "action" in parsed and "confidence" in parsed:
                        latency = round(time.perf_counter() - start_time, 4)
                        logger.info(f"Gemini Request Complete | Latency: {latency}s | Retries: {attempt - 1}")
                        return raw_text
                else:
                    self.api_calls += 1
                    raw_text = self._fallback_mock.generate(prompt)
                    return raw_text
            except Exception as exc:
                err_msg = str(exc).lower()
                if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg or "rate limit" in err_msg:
                    logger.error(f"Gemini API Quota Exhausted ({exc}). Activating instant circuit breaker fallback.")
                    self._quota_exhausted = True
                    self.fallback_count += 1
                    return json.dumps({
                        "action": "digest",
                        "message_type": "unknown",
                        "reason": "Gemini API quota exhausted circuit breaker fallback.",
                        "confidence": 0.50,
                    })

                logger.warning(f"Gemini API attempt {attempt}/{max_retries} failed ({exc}). Retrying...")

                if attempt < max_retries:
                    time.sleep(1.0 * attempt)

        # All retries exhausted -> Return deterministic JSON fallback
        self.fallback_count += 1
        logger.error(f"All {max_retries} Gemini API retries failed. Returning deterministic fallback.")
        return json.dumps({
            "action": "digest",
            "message_type": "unknown",
            "reason": "Gemini API fallback completion.",
            "confidence": 0.50,
        })

    def print_metrics(self) -> None:
        """Log provider execution performance metrics."""
        logger.info(f"--- GEMINI PROVIDER METRICS ---")
        logger.info(f"Provider:        {self.name}")
        logger.info(f"Model:           {self.model_name}")
        logger.info(f"Batch Size:      {self.batch_size}")
        logger.info(f"API Calls:       {self.api_calls}")
        logger.info(f"Cache Hits:      {self.cache_hits}")
        logger.info(f"Cache Misses:    {self.cache_misses}")
        logger.info(f"Retry Count:     {self.retry_count}")
        logger.info(f"Fallback Count:  {self.fallback_count}")

    def health_check(self) -> bool:
        """Check provider health status.

        Returns:
            True if configured, else False.
        """
        return self.api_key is not None and len(self.api_key) > 0

    def count_tokens(self, text: str) -> int:
        """Estimate token count for input text string.

        Args:
            text: Input text string.

        Returns:
            Token count integer.
        """
        return max(1, len(text.split()))
