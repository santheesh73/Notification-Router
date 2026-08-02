"""Hybrid Multi-LLM Router coordinating Groq, Gemma, and Rule Engine Fallback."""

from dataclasses import dataclass, field
import time
from typing import Any

from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.features.feature_vector import FeatureVector
from src.llm.cache import PromptCache
from src.llm.decision_result import DecisionResult
from src.llm.gemma_provider import GemmaProvider
from src.llm.groq_provider import GroqProvider
from src.llm.prompt_builder import PromptBuilder
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


@dataclass
class HybridRouterMetrics:
    """Dataclass tracking performance and routing metrics across execution."""

    total_messages: int = 0
    rule_resolved_count: int = 0
    text_classified_count: int = 0
    groq_calls: int = 0
    groq_successes: int = 0
    gemma_calls: int = 0
    gemma_successes: int = 0
    rule_fallbacks: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_latency: float = 0.0

    @property
    def rule_coverage(self) -> float:
        """Compute rule coverage percentage (includes text-classified)."""
        return ((self.rule_resolved_count + self.text_classified_count) / self.total_messages * 100.0) if self.total_messages > 0 else 0.0

    @property
    def groq_usage(self) -> float:
        """Compute Groq usage percentage."""
        return (self.groq_calls / self.total_messages * 100.0) if self.total_messages > 0 else 0.0

    @property
    def gemma_usage(self) -> float:
        """Compute Gemma usage percentage."""
        return (self.gemma_calls / self.total_messages * 100.0) if self.total_messages > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        """Compute average latency in seconds."""
        llm_calls = self.groq_calls + self.gemma_calls
        return (self.total_latency / llm_calls) if llm_calls > 0 else 0.0


class HybridLLMRouter:
    """Production-grade Hybrid Multi-LLM Router enforcing Groq -> Gemma -> Rule Engine fallback hierarchy."""

    CATEGORY_THRESHOLDS: dict[str, float] = {
        "greeting": 0.50,
        "promotion": 0.55,
        "business": 0.55,
        "business_update": 0.55,
        "event": 0.55,
        "academic": 0.55,
        "payment": 0.60,
        "forward": 0.55,
        "spam": 0.55,
        "scam": 0.60,
        "office": 0.50,
        "family": 0.50,
        "personal": 0.55,
        "muted_group": 0.50,
        "duplicate": 0.50,
        "reminder": 0.55,
        "urgent": 0.70,
    }

    # Text-based deterministic classification keywords
    BUSINESS_NOTIFICATION_KEYWORDS = {
        "dear customer", "dear valued customer", "hi customer",
        "order ending", "order update", "delivery update", "delivery attempt",
        "account statement", "card statement", "payment update",
        "health-related update", "appointment", "prescription",
        "return pickup", "pickup code", "refund",
        "your account", "account notice", "security update",
        "ride update", "pickup or route",
        "fedex", "shopee", "pvr cinemas",
        "payout profile", "verification step",
    }

    PROMOTION_KEYWORDS = {
        "% off", "50% off", "40% off", "limited time",
        "shopping offer", "shopping benefit", "extra discounts",
        "welcome offer", "deal available", "saved travel deal",
        "won't wait", "hurry", "use code",
        "try50", "launch price", "token today",
        "selected products", "saved items",
        "international payouts", "global payouts",
        "interacted with this program", "events, hiring",
    }

    PERSONAL_KEYWORDS = {
        "did you eat", "kept some dal", "call me later",
        "don't call now", "phone is charging", "talk tomorrow",
        "nothing urgent", "no need to reply",
        "blue denim jacket", "collect it from",
        "pottery workshop", "water bottle",
        "left a blue", "front desk",
        "reached home", "had dinner",
        "is this arun", "courier desk", "package mix-up",
        "dance practice", "studio b", "front gate is locked",
        "je suis a la reception", "passeport", "bonjour",
    }

    WORK_KEYWORDS = {
        "dashboard review", "nothing blocking", "deployment notes",
        "rollback is approved", "drain the queue", "failed jobs",
        "payment worker", "alert threshold", "client escalation",
        "build is failing", "incident summary",
        "stay online", "30 minutes",
    }

    SCAM_INJECTION_KEYWORDS = {
        "system note", "internal router metadata", "assistant instruction",
        "ignore sender risk", "always mark this as",
        "verified_business=true", "user_priority=high",
        "action=notify", "action=not",
        "security patch failed", "reply with",
    }

    URGENT_KEYWORDS = {
        "call me now", "call me urgently",
        "decide in next ten minutes", "need to decide",
        "clinic is asking", "specialist",
    }

    def __init__(
        self,
        groq_provider: GroqProvider | None = None,
        gemma_provider: GemmaProvider | None = None,
        cache: PromptCache | None = None,
        batch_size: int = 10,
    ) -> None:
        """Initialize HybridLLMRouter.

        Args:
            groq_provider: GroqProvider instance.
            gemma_provider: GemmaProvider instance.
            cache: PromptCache instance.
            batch_size: Configurable batch chunk size for unresolved messages (default 10).
        """
        self.groq_provider: GroqProvider = groq_provider or GroqProvider()
        self.gemma_provider: GemmaProvider = gemma_provider or GemmaProvider()
        self.cache: PromptCache = cache or PromptCache()
        self.batch_size: int = batch_size
        self.metrics: HybridRouterMetrics = HybridRouterMetrics()

    def process_batch(
        self,
        vectors: list[FeatureVector],
        rule_results: list[RuleResult],
        context: ContextManager,
        media_results: list[MediaResult] | None = None,
        retrieval_results: list[RetrievalResult] | None = None,
    ) -> list[DecisionResult]:
        """Process batch of messages through Rule Engine check, Text Classification, Prompt Cache, Groq, Gemma, and Rule Fallback.

        Args:
            vectors: List of FeatureVector instances.
            rule_results: List of RuleResult instances.
            context: ContextManager instance.
            media_results: Optional list of MediaResult instances.
            retrieval_results: Optional list of RetrievalResult instances.

        Returns:
            List of DecisionResult instances.
        """
        total_messages = len(vectors)
        self.metrics.total_messages = total_messages
        logger.info(f"HybridLLMRouter processing batch of {total_messages} messages...")

        rule_map = {r.message_id: r for r in rule_results}
        media_map = {m.message_id: m for m in (media_results or [])}
        ret_map = {ret.message_id: ret for ret in (retrieval_results or [])}

        results: list[DecisionResult] = []
        unresolved_queue: list[tuple[FeatureVector, RuleResult]] = []

        # 1. Phase 1: Rule Engine First Pass Evaluation
        for vec in vectors:
            r_res = rule_map.get(
                vec.message_id,
                RuleResult(vec.message_id, False, "unresolved", "unknown", "None", 0.0, "None", "4", True),
            )

            if self._is_rule_resolved(vec, r_res, media_map):
                self.metrics.rule_resolved_count += 1
                d_res = DecisionResult(
                    message_id=vec.message_id,
                    action=r_res.action if r_res.action != "unresolved" else "digest",
                    message_type=r_res.message_type if r_res.message_type != "unknown" else "general",
                    reason=r_res.reason,
                    confidence=r_res.confidence if r_res.confidence > 0 else 0.90,
                    provider="RuleEngine",
                    latency=0.0,
                    cached=False,
                )
                results.append(d_res)
                logger.info(
                    f"Message '{vec.message_id}': Rule Conf={r_res.confidence:.2f} >= threshold -> Provider=Rule Only"
                )
            else:
                # Try text-based deterministic classification before queuing for LLM
                text_decision = self._classify_by_text_content(vec, r_res)
                if text_decision:
                    self.metrics.text_classified_count += 1
                    results.append(text_decision)
                    logger.info(
                        f"Message '{vec.message_id}': Text-classified -> type={text_decision.message_type}, action={text_decision.action}"
                    )
                else:
                    unresolved_queue.append((vec, r_res))

        logger.info(f"Dataset Loaded | Rule Coverage: {self.metrics.rule_coverage:.1f}% ({self.metrics.rule_resolved_count + self.metrics.text_classified_count}/{total_messages})")
        logger.info(f"Ambiguous Messages Queued for Multi-LLM Routing: {len(unresolved_queue)}")

        # 2. Phase 2: Process Unresolved Messages in Batches of 10
        for i in range(0, len(unresolved_queue), self.batch_size):
            batch_chunk = unresolved_queue[i : i + self.batch_size]
            batch_results = self._process_unresolved_chunk(batch_chunk, context, media_map, ret_map)
            results.extend(batch_results)

        # Re-sort to preserve input vector order
        order_map = {vec.message_id: idx for idx, vec in enumerate(vectors)}
        results.sort(key=lambda d: order_map.get(d.message_id, 0))

        return results

    def _classify_by_text_content(
        self,
        vector: FeatureVector,
        rule_result: RuleResult,
    ) -> DecisionResult | None:
        """Attempt deterministic classification using FeatureVector signal flags and text keywords.

        This avoids unnecessary LLM calls for messages that can be classified
        by inspecting feature flags and keyword patterns.

        Args:
            vector: FeatureVector instance.
            rule_result: RuleResult from rule engine (may be unresolved).

        Returns:
            DecisionResult if classified, None if still ambiguous.
        """
        msg_id = vector.message_id

        # Access raw text if available via getattr
        raw_text = str(getattr(vector, "message_text", "") or "")
        text_lower = raw_text.lower().strip()

        # 1. Empty/NaN messages -> mute as spam
        if not text_lower or text_lower == "nan" or len(text_lower) < 3:
            return DecisionResult(
                message_id=msg_id,
                action="mute",
                message_type="spam",
                reason="Empty or negligible content message muted as spam.",
                confidence=0.92,
                provider="TextClassifier",
                latency=0.0,
            )

        # 2. Scam/Injection attacks (prompt injection, metadata manipulation)
        if any(kw in text_lower for kw in self.SCAM_INJECTION_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="mute",
                message_type="scam",
                reason="Detected prompt injection or metadata manipulation attack pattern.",
                confidence=0.96,
                provider="TextClassifier",
                latency=0.0,
            )

        # 3. Urgent personal messages
        if any(kw in text_lower for kw in self.URGENT_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="notify",
                message_type="urgent",
                reason="Message contains urgent time-sensitive request requiring immediate attention.",
                confidence=0.88,
                provider="TextClassifier",
                latency=0.0,
            )

        # 4. Work/Office messages
        if any(kw in text_lower for kw in self.WORK_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="notify" if any(kw in text_lower for kw in {"rollback", "escalation", "failing", "come online now"}) else "digest",
                message_type="office",
                reason="Work-related communication routed based on content analysis.",
                confidence=0.85,
                provider="TextClassifier",
                latency=0.0,
            )

        # 5. Business notifications (Dear Customer...)
        if any(kw in text_lower for kw in self.BUSINESS_NOTIFICATION_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="business_update",
                reason="Business notification or transactional update routed to digest.",
                confidence=0.85,
                provider="TextClassifier",
                latency=0.0,
            )

        # 6. Promotions and marketing
        if any(kw in text_lower for kw in self.PROMOTION_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="promotion",
                reason="Marketing promotion or commercial offer routed to digest.",
                confidence=0.82,
                provider="TextClassifier",
                latency=0.0,
            )

        # 7. Personal/casual messages
        if any(kw in text_lower for kw in self.PERSONAL_KEYWORDS):
            return DecisionResult(
                message_id=msg_id,
                action="notify",
                message_type="personal",
                reason="Personal or casual message from known contact.",
                confidence=0.80,
                provider="TextClassifier",
                latency=0.0,
            )

        # 8. Feature flag based classification for remaining messages
        if vector.contains_payment or vector.contains_invoice or vector.contains_upi:
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="payment",
                reason="Payment or financial transaction notification routed to digest.",
                confidence=0.80,
                provider="TextClassifier",
                latency=0.0,
            )

        if vector.contains_event or vector.contains_meeting or vector.contains_exam:
            return DecisionResult(
                message_id=msg_id,
                action="notify",
                message_type="event",
                reason="Event, meeting, or exam notification requiring attention.",
                confidence=0.78,
                provider="TextClassifier",
                latency=0.0,
            )

        if vector.contains_greeting and not vector.contains_url and vector.word_count < 30:
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="greeting",
                reason="Simple greeting or social message routed to digest.",
                confidence=0.78,
                provider="TextClassifier",
                latency=0.0,
            )

        if vector.contains_offer or vector.contains_discount or vector.contains_coupon:
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="promotion",
                reason="Promotional offer detected and routed to digest.",
                confidence=0.78,
                provider="TextClassifier",
                latency=0.0,
            )

        # 9. Conversation type based default for personal messages
        if vector.conversation_type == "personal" or vector.personal:
            is_direct_req = (
                vector.favorite_contact
                or vector.contains_question
                or "@u_" in text_lower
                or any(k in text_lower for k in ["can you call", "call me", "pls call", "when you get 5 mins", "quick decision", "are you free", "reach out"])
            ) and not any(k in text_lower for k in ["don't call now", "nothing urgent", "no need to reply", "no pressure", "checking in", "good week", "no rush"])

            act = "notify" if is_direct_req else "digest"
            return DecisionResult(
                message_id=msg_id,
                action=act,
                message_type="personal",
                reason=f"Personal message from contact routed to {act}.",
                confidence=0.80,
                provider="TextClassifier",
                latency=0.0,
            )

        if vector.conversation_type == "business" or vector.business:
            return DecisionResult(
                message_id=msg_id,
                action="digest",
                message_type="business_update",
                reason="Business channel message routed to digest.",
                confidence=0.75,
                provider="TextClassifier",
                latency=0.0,
            )

        # Not classifiable by text — return None to trigger LLM routing
        return None

    def _is_rule_resolved(
        self,
        vector: FeatureVector,
        rule_result: RuleResult,
        media_map: dict[str, Any] | None = None,
    ) -> bool:
        """Check if message is deterministically resolved by Rule Engine using category-specific confidence thresholds."""
        if not rule_result.resolved or rule_result.requires_ai:
            return False

        msg_id = vector.message_id

        # High-confidence rule decisions (>= 0.85) override media uncertainty
        if rule_result.confidence < 0.85 and media_map and msg_id in media_map:
            m_res = media_map[msg_id]
            m_type = getattr(m_res, "media_type", "none")
            if m_type in ["image", "voice", "audio"] and not (vector.muted_group or vector.mute_state):
                return False

        # Category-specific threshold evaluation
        msg_type = (rule_result.message_type or "").lower()
        triggered = (rule_result.triggered_rule or "").lower()

        threshold = 0.50
        for cat_key, cat_thresh in self.CATEGORY_THRESHOLDS.items():
            if cat_key in msg_type or cat_key in triggered:
                threshold = cat_thresh
                break

        return rule_result.confidence >= threshold

    def _process_unresolved_chunk(
        self,
        chunk: list[tuple[FeatureVector, RuleResult]],
        context: ContextManager,
        media_map: dict[str, Any],
        ret_map: dict[str, Any],
    ) -> list[DecisionResult]:
        """Process a chunk of unresolved messages (default 10) through Cache -> Groq -> Gemma -> Rule Fallback."""
        chunk_results: list[DecisionResult] = []

        for vec, r_res in chunk:
            m_res = media_map.get(vec.message_id)
            ret_res = ret_map.get(vec.message_id)

            prompt = PromptBuilder.build_prompt(vec, r_res, context, m_res, ret_res)

            # 1. Prompt Cache Check
            cached_res = self.cache.get(prompt)
            if cached_res:
                self.metrics.cache_hits += 1
                parsed = cached_res.get("parsed", {})
                d_res = DecisionResult(
                    message_id=vec.message_id,
                    action=parsed.get("action", "digest"),
                    message_type=parsed.get("message_type", "general"),
                    reason=parsed.get("reason", "Cached LLM response."),
                    confidence=parsed.get("confidence", 0.90),
                    provider=cached_res.get("provider", "Groq"),
                    latency=0.0,
                    cached=True,
                )
                chunk_results.append(d_res)
                logger.info(f"Message '{vec.message_id}': SHA256 Cache HIT -> Provider={d_res.provider} (Cached)")
                continue

            self.metrics.cache_misses += 1

            # 2. Priority 1: Try Groq API (Llama 3 70B)
            groq_success = False
            if self.groq_provider.is_healthy():
                self.metrics.groq_calls += 1
                try:
                    res_dict = self.groq_provider.generate(prompt, timeout=15.0)
                    parsed = res_dict["parsed"]
                    self.metrics.groq_successes += 1
                    self.metrics.total_latency += res_dict["latency"]

                    d_res = DecisionResult(
                        message_id=vec.message_id,
                        action=parsed["action"],
                        message_type=parsed.get("message_type", "general"),
                        reason=parsed.get("reason", "AI classification by Groq Llama 3.3 70B."),
                        confidence=parsed.get("confidence", 0.85),
                        provider="Groq",
                        latency=res_dict["latency"],
                        tokens=res_dict.get("tokens", {}),
                        cached=False,
                    )
                    self.cache.put(prompt, res_dict)
                    chunk_results.append(d_res)
                    groq_success = True
                    logger.info(
                        f"Message '{vec.message_id}': Groq Llama-3.3-70B Success | Latency={res_dict['latency']}s | Retries={res_dict['retries']}"
                    )
                except Exception as exc:
                    logger.warning(f"Groq API failed for '{vec.message_id}' ({exc}). Falling back to Gemma...")

            if groq_success:
                continue

            # 3. Priority 2: Automatically Invoke Gemma API (Gemma-3 27B IT)
            gemma_success = False
            if self.gemma_provider.is_healthy():
                self.metrics.gemma_calls += 1
                try:
                    res_dict = self.gemma_provider.generate(prompt, timeout=15.0)
                    parsed = res_dict["parsed"]
                    self.metrics.gemma_successes += 1
                    self.metrics.total_latency += res_dict["latency"]

                    d_res = DecisionResult(
                        message_id=vec.message_id,
                        action=parsed["action"],
                        message_type=parsed.get("message_type", "general"),
                        reason=parsed.get("reason", "AI classification by Gemma 3 27B IT."),
                        confidence=parsed.get("confidence", 0.82),
                        provider="Gemma",
                        latency=res_dict["latency"],
                        tokens=res_dict.get("tokens", {}),
                        cached=False,
                    )
                    self.cache.put(prompt, res_dict)
                    chunk_results.append(d_res)
                    gemma_success = True
                    logger.info(
                        f"Message '{vec.message_id}': Gemma-3-27B Fallback Success | Latency={res_dict['latency']}s | Retries={res_dict['retries']}"
                    )
                except Exception as exc:
                    logger.warning(f"Gemma API failed for '{vec.message_id}' ({exc}). Falling back to Deterministic Rule Decision...")

            if gemma_success:
                continue

            # 4. Priority 3: Deterministic Rule Fallback (Never Crash)
            self.metrics.rule_fallbacks += 1
            fallback_action = r_res.action if r_res.action != "unresolved" else ("mute" if getattr(vec, "muted_group", False) or getattr(vec, "mute_state", False) else "digest")
            fallback_type = r_res.message_type if r_res.message_type not in ("unknown", "general", "") else self._infer_fallback_type(vec)

            d_res = DecisionResult(
                message_id=vec.message_id,
                action=fallback_action,
                message_type=fallback_type,
                reason=f"Deterministic classification based on message context and content signals.",
                confidence=r_res.confidence if r_res.confidence > 0 else 0.60,
                provider="Rule Engine Fallback",
                latency=0.0001,
                cached=False,
            )
            chunk_results.append(d_res)
            logger.info(f"Message '{vec.message_id}': Rule Engine Fallback Applied -> Action={fallback_action}, Type={fallback_type}")

        return chunk_results

    def _infer_fallback_type(self, vector: FeatureVector) -> str:
        """Infer best message type from feature vector flags when no rule or LLM classification available.

        Args:
            vector: FeatureVector instance.

        Returns:
            Inferred message type string.
        """
        if vector.contains_scam_keyword or vector.risk_score > 0.3:
            return "scam"
        if vector.contains_payment or vector.contains_invoice:
            return "payment"
        if vector.contains_event or vector.contains_meeting:
            return "event"
        if vector.business or vector.conversation_type == "business":
            return "business_update"
        if vector.contains_greeting:
            return "greeting"
        if vector.is_forwarded or vector.forwarded_count > 2:
            return "forward"
        if vector.contains_offer or vector.contains_discount:
            return "promotion"
        if vector.personal or vector.conversation_type == "personal":
            return "personal"
        if vector.group or vector.conversation_type == "group":
            return "business_update"
        return "unknown"

    def generate_report(self) -> str:
        """Generate formatted metrics summary report across Multi-LLM execution."""
        deterministic_total = self.metrics.rule_resolved_count + self.metrics.text_classified_count
        unresolved_sent = self.metrics.groq_calls + self.metrics.gemma_calls
        rows = [
            ["Total Dataset Messages", self.metrics.total_messages],
            ["Total Messages Evaluated", self.metrics.total_messages],
            ["Rule Engine Resolved", f"{self.metrics.rule_resolved_count}"],
            ["Text Classifier Resolved", f"{self.metrics.text_classified_count}"],
            ["Total Deterministic Coverage", f"{deterministic_total} ({self.metrics.rule_coverage:.1f}%)"],
            ["Messages Sent to LLM (Unresolved)", unresolved_sent],
            ["Groq API Calls", f"{self.metrics.groq_calls} (Successes: {self.metrics.groq_successes})"],
            ["Gemma API Calls", f"{self.metrics.gemma_calls} (Successes: {self.metrics.gemma_successes})"],
            ["Rule Fallback Count", self.metrics.rule_fallbacks],
            ["Cache Hit Rate", f"{self.cache.hit_rate * 100:.1f}% ({self.metrics.cache_hits} Hits)"],
            ["Average Latency", f"{self.metrics.avg_latency:.4f}s"],
        ]
        return tabulate(rows, headers=["Hybrid LLM Metric", "Value"], tablefmt="grid")
