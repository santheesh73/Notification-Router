"""AI Decision Orchestrator with Quota Protection and Category Heuristic Filtering."""

import time
from typing import Any

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.llm.llm_cache import LLMCache
from src.llm.llm_provider import LLMProvider, get_provider
from src.llm.prompt_builder import PromptBuilder
from src.llm.retry_handler import RetryHandler
from src.llm.token_counter import TokenCounter
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


class DecisionOrchestrator:
    """AI Decision Orchestrator for contextual reasoning over unresolved notification messages."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        prompt_builder: PromptBuilder | None = None,
        retry_handler: RetryHandler | None = None,
        cache: LLMCache | None = None,
        token_counter: TokenCounter | None = None,
    ) -> None:
        """Initialize DecisionOrchestrator.

        Args:
            provider: LLMProvider instance.
            prompt_builder: PromptBuilder instance.
            retry_handler: RetryHandler instance.
            cache: LLMCache instance.
            token_counter: TokenCounter instance.
        """
        self.provider: LLMProvider = provider or get_provider()
        self.prompt_builder: PromptBuilder = prompt_builder or PromptBuilder()
        self.retry_handler: RetryHandler = retry_handler or RetryHandler(max_retries=3)
        self.cache: LLMCache = cache or LLMCache()
        self.token_counter: TokenCounter = token_counter or TokenCounter()

    def process_message(
        self,
        vector: FeatureVector,
        rule_result: RuleResult,
        context: ContextManager,
        media_result: MediaResult | None = None,
        retrieval_result: RetrievalResult | None = None,
    ) -> DecisionResult:
        """Process a message and orchestrate AI decision reasoning if unresolved by Rule Engine.

        Args:
            vector: Extracted FeatureVector instance.
            rule_result: RuleResult from Phase 4 Rule Engine.
            context: ContextManager instance.
            media_result: MediaResult instance from Phase 6 or None.
            retrieval_result: RetrievalResult instance from Phase 5 or None.

        Returns:
            Constructed DecisionResult object.
        """
        # 1. Skip LLM if Rule Engine already resolved decision deterministically
        if rule_result.resolved:
            logger.debug(f"Message '{vector.message_id}' resolved by Rule Engine -> Skipping LLM.")
            return DecisionResult(
                message_id=vector.message_id,
                action=rule_result.action,
                message_type=rule_result.message_type,
                reason=rule_result.reason,
                confidence=rule_result.confidence,
                provider="RuleEngine",
                latency=0.0,
                tokens={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cached=False,
            )

        # 2. Skip LLM if Rule confidence >= 0.85
        if rule_result.confidence >= 0.85:
            logger.debug(f"Rule Engine confidence high ({rule_result.confidence:.2f} >= 0.85) -> Skipping LLM.")
            return DecisionResult(
                message_id=vector.message_id,
                action=rule_result.action if rule_result.action != "unresolved" else "digest",
                message_type=rule_result.message_type if rule_result.message_type != "unknown" else "general",
                reason=rule_result.reason,
                confidence=rule_result.confidence,
                provider="RuleEngine",
                latency=0.0,
                tokens={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cached=False,
            )

        # 3. Skip LLM for specific categories (greetings, promotions, scams, spam, forwards, muted)
        triggered = (rule_result.triggered_rule or "").lower()
        msg_type = (rule_result.message_type or "").lower()

        is_skip_category = (
            "greeting" in triggered or "greeting" in msg_type or vector.contains_greeting or
            "promotion" in triggered or "promotion" in msg_type or vector.contains_discount or vector.contains_offer or
            "scam" in triggered or "scam" in msg_type or vector.contains_scam_keyword or
            "spam" in triggered or "spam" in msg_type or
            "forward" in triggered or vector.is_forwarded or vector.forwarded_count > 0 or
            "muted" in triggered or vector.muted_group or vector.mute_state
        )

        if is_skip_category:
            logger.debug(f"Message '{vector.message_id}' matches category heuristic ({msg_type}/{triggered}) -> Skipping LLM.")
            act = rule_result.action if rule_result.action != "unresolved" else ("mute" if (vector.muted_group or vector.mute_state or "scam" in msg_type or "spam" in msg_type) else "digest")
            m_type = rule_result.message_type if rule_result.message_type != "unknown" else "general"
            return DecisionResult(
                message_id=vector.message_id,
                action=act,
                message_type=m_type,
                reason=f"Skipped LLM for category heuristic: {rule_result.reason}",
                confidence=0.85,
                provider="RuleEngine",
                latency=0.0,
                tokens={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cached=False,
            )

        # 4. Build Structured Prompt
        prompt = self.prompt_builder.build_prompt(
            vector=vector,
            rule_result=rule_result,
            media_result=media_result,
            retrieval_result=retrieval_result,
            context=context,
        )

        # 5. Check LLM Cache
        cached_res = self.cache.get(prompt)
        if cached_res:
            if hasattr(self.provider, "cache_hits"):
                self.provider.cache_hits += 1
            return cached_res

        if hasattr(self.provider, "cache_misses"):
            self.provider.cache_misses += 1

        # 6. Measure Latency & Execute LLM via RetryHandler
        start_time = time.perf_counter()
        parsed_dict, attempts = self.retry_handler.execute_with_retry(self.provider, prompt)
        latency_sec = round(time.perf_counter() - start_time, 4)

        # 7. Track Token Metrics
        p_tokens = self.token_counter.estimate_tokens(prompt)
        c_tokens = self.token_counter.estimate_tokens(str(parsed_dict))
        self.token_counter.record_usage(p_tokens, c_tokens)

        token_info = {
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": p_tokens + c_tokens,
        }

        # 8. Construct DecisionResult
        result = DecisionResult(
            message_id=vector.message_id,
            action=parsed_dict.get("action", "digest"),
            message_type=parsed_dict.get("message_type", "unknown"),
            reason=parsed_dict.get("reason", "Contextual LLM routing decision."),
            confidence=float(parsed_dict.get("confidence", 0.80)),
            provider=self.provider.name,
            latency=latency_sec,
            tokens=token_info,
            cached=False,
        )

        # 9. Store in Cache
        self.cache.set(prompt, result)
        logger.info(
            f"AI Orchestrator decision for '{vector.message_id}': action={result.action}, "
            f"type={result.message_type}, conf={result.confidence:.2f}, attempts={attempts}, latency={latency_sec}s"
        )
        return result
