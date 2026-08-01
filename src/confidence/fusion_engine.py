"""Decision Fusion Engine."""

from dataclasses import asdict, dataclass, field
import time
from typing import Any

from tabulate import tabulate

from src.builders.context_manager import ContextManager
from src.confidence.confidence_engine import ConfidenceEngine
from src.confidence.conflict_resolver import ConflictResolver
from src.confidence.final_decision import FinalDecision
from src.confidence.validation import DecisionValidator
from src.features.feature_vector import FeatureVector
from src.llm.decision_result import DecisionResult
from src.media.media_result import MediaResult
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


@dataclass
class FusionValidationReport:
    """Dataclass holding validation report for final decision fusion outputs."""

    missing_message_ids: list[str] = field(default_factory=list)
    invalid_actions: list[str] = field(default_factory=list)
    invalid_confidences: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors are found."""
        return (
            len(self.missing_message_ids) == 0
            and len(self.invalid_actions) == 0
            and len(self.invalid_confidences) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class DecisionFusionEngine:
    """Primary Decision Fusion Engine combining Rule Engine, Media, Evidence, and LLM signals."""

    def __init__(
        self,
        resolver: ConflictResolver | None = None,
        confidence_engine: ConfidenceEngine | None = None,
        validator: DecisionValidator | None = None,
    ) -> None:
        """Initialize DecisionFusionEngine.

        Args:
            resolver: ConflictResolver instance.
            confidence_engine: ConfidenceEngine instance.
            validator: DecisionValidator instance.
        """
        self.resolver: ConflictResolver = resolver or ConflictResolver()
        self.confidence_engine: ConfidenceEngine = confidence_engine or ConfidenceEngine()
        self.validator: DecisionValidator = validator or DecisionValidator()

    def fuse_decision(
        self,
        vector: FeatureVector,
        rule_result: RuleResult,
        llm_result: DecisionResult,
        media_result: MediaResult | None,
        retrieval_result: RetrievalResult | None,
        context: ContextManager,
    ) -> FinalDecision:
        """Fuse multi-source signals for a single message into FinalDecision.

        Args:
            vector: Extracted FeatureVector instance.
            rule_result: Phase 4 RuleResult.
            llm_result: Phase 7 DecisionResult.
            media_result: Phase 6 MediaResult or None.
            retrieval_result: Phase 5 RetrievalResult or None.
            context: ContextManager instance.

        Returns:
            Constructed FinalDecision object.
        """
        start_time = time.perf_counter()

        # 1. Resolve Conflict and determine Action, Type, Reason, Source
        act, m_type, raw_reason, d_source, ai_resolved = self.resolver.resolve(
            rule_result=rule_result,
            llm_result=llm_result,
            media_result=media_result,
            vector=vector,
        )

        # 2. Compute Calibrated Confidence
        calibrated_conf = self.confidence_engine.compute_confidence(
            rule_result=rule_result,
            llm_result=llm_result,
            retrieval_result=retrieval_result,
            media_result=media_result,
            vector=vector,
            action=act,
            message_type=m_type,
        )

        # 3. Sanitize Reason and Evidence IDs
        clean_reason = self.validator.validate_reason(raw_reason)
        raw_ev = retrieval_result.evidence_message_ids if retrieval_result else []
        clean_ev = self.validator.validate_evidence_ids(raw_ev)

        proc_time = round(time.perf_counter() - start_time, 4)

        result = FinalDecision(
            message_id=vector.message_id,
            action=act,
            message_type=m_type,
            reason=clean_reason,
            confidence=calibrated_conf,
            evidence_message_ids=clean_ev,
            decision_source=d_source,
            rule_used=rule_result.triggered_rule if rule_result.resolved else "None",
            llm_provider=llm_result.provider if llm_result else "None",
            resolved_by_ai=ai_resolved,
            processing_time=proc_time,
        )

        logger.debug(f"Fused decision for '{vector.message_id}': action={act}, conf={calibrated_conf:.4f}, source={d_source}")
        return result

    def fuse_batch(
        self,
        vectors: list[FeatureVector],
        rule_results: list[RuleResult],
        llm_results: list[DecisionResult],
        context: ContextManager,
        media_results: list[MediaResult] | None = None,
        retrieval_results: list[RetrievalResult] | None = None,
    ) -> list[FinalDecision]:
        """Fuse a batch of message signals into FinalDecisions.

        Args:
            vectors: List of FeatureVectors.
            rule_results: List of Phase 4 RuleResults.
            llm_results: List of Phase 7 DecisionResults.
            context: ContextManager instance.
            media_results: Optional list of Phase 6 MediaResults.
            retrieval_results: Optional list of Phase 5 RetrievalResults.

        Returns:
            List of FinalDecision instances.
        """
        logger.info(f"Fusing decision signals for {len(vectors)} messages...")

        rule_map = {r.message_id: r for r in rule_results}
        llm_map = {l.message_id: l for l in llm_results}
        media_map = {m.message_id: m for m in (media_results or [])}
        ret_map = {ret.message_id: ret for ret in (retrieval_results or [])}

        decisions: list[FinalDecision] = []
        for vec in vectors:
            r_res = rule_map.get(
                vec.message_id,
                RuleResult(vec.message_id, False, "unresolved", "unknown", "None", 0.0, "None", "4", True),
            )
            l_res = llm_map.get(
                vec.message_id,
                DecisionResult(vec.message_id, "digest", "unknown", "Fallback", 0.50),
            )
            m_res = media_map.get(vec.message_id)
            ret_res = ret_map.get(vec.message_id)

            f_dec = self.fuse_decision(
                vector=vec,
                rule_result=r_res,
                llm_result=l_res,
                media_result=m_res,
                retrieval_result=ret_res,
                context=context,
            )
            decisions.append(f_dec)

        logger.success(f"Successfully fused {len(decisions)} final decisions.")
        return decisions

    def validate(self, decisions: list[FinalDecision]) -> FusionValidationReport:
        """Validate FinalDecision list outputs.

        Args:
            decisions: List of FinalDecision instances.

        Returns:
            FusionValidationReport object.
        """
        report = FusionValidationReport()

        for dec in decisions:
            if not dec.message_id:
                report.missing_message_ids.append(dec.message_id)

            valid_ok, err_msg = self.validator.validate_decision(dec.action, dec.message_type, dec.confidence)
            if not valid_ok:
                if "action" in err_msg:
                    report.invalid_actions.append(f"{dec.message_id}: {dec.action}")
                if "bounds" in err_msg:
                    report.invalid_confidences.append(f"{dec.message_id}: {dec.confidence}")

        logger.info(f"Fusion validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self, decisions: list[FinalDecision]) -> str:
        """Generate statistical summary report across FinalDecision outputs.

        Args:
            decisions: List of FinalDecision instances.

        Returns:
            Formatted ASCII summary table string.
        """
        if not decisions:
            return "No FinalDecisions available for summary."

        total_d = len(decisions)
        rule_cnt = sum(1 for d in decisions if d.decision_source == "RULE_ENGINE")
        llm_cnt = sum(1 for d in decisions if d.decision_source == "LLM")
        fused_cnt = sum(1 for d in decisions if d.decision_source == "FUSED")
        fallback_cnt = sum(1 for d in decisions if d.decision_source == "FALLBACK")

        avg_conf = sum(d.confidence for d in decisions) / total_d
        avg_proc_time = sum(d.processing_time for d in decisions) / total_d
        evidence_cov = sum(1 for d in decisions if len(d.evidence_message_ids) > 0)

        rows = [
            ["Total Final Decisions", total_d],
            ["Rule Engine Sourced", f"{rule_cnt} ({(rule_cnt / total_d) * 100:.1f}%)"],
            ["LLM Sourced", f"{llm_cnt} ({(llm_cnt / total_d) * 100:.1f}%)"],
            ["Fused Sourced", f"{fused_cnt} ({(fused_cnt / total_d) * 100:.1f}%)"],
            ["Fallback Sourced", f"{fallback_cnt} ({(fallback_cnt / total_d) * 100:.1f}%)"],
            ["Average Calibrated Confidence", f"{avg_conf:.4f}"],
            ["Average Processing Time", f"{avg_proc_time:.6f}s"],
            ["Conflict / Fused Overrides", fused_cnt],
            ["Evidence Coverage Rate", f"{evidence_cov} ({(evidence_cov / total_d) * 100:.1f}%)"],
        ]

        return tabulate(rows, headers=["Fusion Metric", "Statistical Value"], tablefmt="grid")
