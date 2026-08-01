"""End-to-End Execution Pipeline with Checkpoint State Recovery and Output Pre/Post-Validation."""

from pathlib import Path
import time
from typing import Any

from src.builders.context_manager import ContextManager
from src.confidence.final_decision import FinalDecision
from src.confidence.fusion_engine import DecisionFusionEngine
from src.features.feature_pipeline import FeaturePipeline
from src.loaders.load_data import DataRepository
from src.llm.decision_result import DecisionResult
from src.llm.hybrid_router import HybridLLMRouter
from src.media.media_manager import MediaManager
from src.media.media_result import MediaResult
from src.output.output_writer import OutputWriter
from src.pipeline.batch_processor import BatchProcessor
from src.pipeline.checkpoint_manager import CheckpointManager
from src.pipeline.execution_report import ExecutionReportGenerator
from src.pipeline.progress_tracker import ProgressTracker
from src.retrieval.retrieval_engine import RetrievalEngine
from src.retrieval.retrieval_result import RetrievalResult
from src.rules.rule_engine import NotificationRuleEngine
from src.rules.rule_result import RuleResult
from src.utils.logger import logger


class ExecutionPipeline:
    """End-to-End Execution Pipeline for WhatsApp Message Notification Router."""

    def __init__(
        self,
        repository: DataRepository,
        context: ContextManager,
        batch_size: int = 50,
        checkpoint_interval: int = 25,
        output_writer: OutputWriter | None = None,
        feature_pipeline: FeaturePipeline | None = None,
        rule_engine: NotificationRuleEngine | None = None,
        retrieval_engine: RetrievalEngine | None = None,
        media_manager: MediaManager | None = None,
        hybrid_router: HybridLLMRouter | None = None,
        fusion_engine: DecisionFusionEngine | None = None,
    ) -> None:
        """Initialize ExecutionPipeline.

        Args:
            repository: DataRepository instance.
            context: ContextManager instance.
            batch_size: Configurable batch chunk size (default 50).
            checkpoint_interval: Checkpoint save interval (default 25).
            output_writer: OutputWriter instance.
            feature_pipeline: FeaturePipeline instance.
            rule_engine: NotificationRuleEngine instance.
            retrieval_engine: RetrievalEngine instance.
            media_manager: MediaManager instance.
            hybrid_router: HybridLLMRouter instance for Groq -> Gemma -> Rule Fallback routing.
            fusion_engine: DecisionFusionEngine instance.
        """
        self.repository: DataRepository = repository
        self.context: ContextManager = context

        self.feature_pipeline: FeaturePipeline = feature_pipeline or FeaturePipeline(context)
        self.rule_engine: NotificationRuleEngine = rule_engine or NotificationRuleEngine()
        self.retrieval_engine: RetrievalEngine = retrieval_engine or RetrievalEngine()
        self.media_manager: MediaManager = media_manager or MediaManager(repository=repository)
        self.hybrid_router: HybridLLMRouter = hybrid_router or HybridLLMRouter(batch_size=10)
        self.fusion_engine: DecisionFusionEngine = fusion_engine or DecisionFusionEngine()

        self.output_writer: OutputWriter = output_writer or OutputWriter()
        self.batch_processor: BatchProcessor = BatchProcessor(batch_size=batch_size)
        self.checkpoint_manager: CheckpointManager = CheckpointManager(interval=checkpoint_interval)
        self.report_generator: ExecutionReportGenerator = ExecutionReportGenerator()

    def run(self, resume: bool = True, overwrite_output: bool = True) -> list[FinalDecision]:
        """Execute end-to-end routing pipeline across all messages in dataset.

        Args:
            resume: Set to True to load state from checkpoint if available.
            overwrite_output: Set to True to overwrite output CSV on fresh run.

        Returns:
            List of generated FinalDecision instances.
        """
        messages_df = self.repository.get_dataframe("messages")
        total_messages = len(messages_df)
        logger.info(f"Starting End-to-End Execution Pipeline for {total_messages} messages...")

        # 1. Clear checkpoint if overwrite_output requested
        if overwrite_output:
            self.checkpoint_manager.clear_checkpoint()
            resume = False

        # 2. Load Checkpoint if resuming
        last_processed_idx = -1
        decisions: list[FinalDecision] = []
        if resume:
            last_processed_idx, decisions = self.checkpoint_manager.load_checkpoint()

        processed_set: set[str] = {d.message_id for d in decisions}
        tracker = ProgressTracker(total_messages=total_messages)

        # Restore progress tracker stats from loaded decisions
        for d in decisions:
            tracker.update(
                d.message_id,
                resolved_by_rule=(d.decision_source == "RULE_ENGINE"),
                resolved_by_ai=d.resolved_by_ai,
                failed=(d.decision_source == "FALLBACK"),
            )

        # 3. Process Remaining Messages
        for idx, row in messages_df.iterrows():
            msg_dict = row.to_dict()
            msg_id = str(msg_dict.get("message_id", f"MSG_{idx:03d}"))

            # Resume Checkpoint Skip
            if idx <= last_processed_idx or msg_id in processed_set:
                logger.debug(f"Skipping message '{msg_id}' at index {idx} (already in checkpoint).")
                continue

            # Process Message with 100% Exception Safety
            final_dec = self._process_single_message_safe(msg_dict, msg_id)
            decisions.append(final_dec)
            processed_set.add(msg_id)

            # Update Tracker
            resolved_rule = final_dec.decision_source == "RULE_ENGINE"
            resolved_ai = final_dec.resolved_by_ai
            is_failed = final_dec.decision_source == "FALLBACK"

            tracker.update(msg_id, resolved_by_rule=resolved_rule, resolved_by_ai=resolved_ai, failed=is_failed)

            # Checkpoint Save Every 25 Messages
            if len(decisions) % self.checkpoint_manager.interval == 0:
                self.checkpoint_manager.save_checkpoint(idx, decisions)

        # 4. Write all predictions cleanly in write mode ('w') - NEVER append
        self.output_writer.write_all(decisions, expected_count=total_messages)

        # 5. Generate Execution Report & Clear Checkpoint
        self.report_generator.generate_report(decisions, tracker)
        self.checkpoint_manager.clear_checkpoint()

        logger.success(f"Execution Pipeline completed successfully. Output written to: {self.output_writer.output_path}")
        return decisions

    def _process_single_message_safe(self, msg_dict: dict[str, Any], msg_id: str) -> FinalDecision:
        """Process single message through all sub-engines with Hybrid Multi-LLM Router.

        Uses Groq -> Gemma -> Rule Fallback hierarchy instead of legacy DecisionOrchestrator.

        Args:
            msg_dict: Message record dictionary.
            msg_id: Message identifier string.

        Returns:
            Constructed FinalDecision object (or safe fallback).
        """
        try:
            # Step 1: Feature Extraction
            vector = self.feature_pipeline.process(msg_dict)

            # Step 2: Historical Evidence Retrieval & Multimodal Media Processing
            ret_res: RetrievalResult | None = self.retrieval_engine.retrieve(vector, self.context, top_k=3)
            med_res: MediaResult | None = self.media_manager.process_media(msg_dict, repository=self.repository)

            # Step 3: Rule Engine
            rule_res = self.rule_engine.route(vector, self.context)

            # Step 4: Category-Specific Threshold Check & Unresolved Fallthrough
            llm_res: DecisionResult

            is_rule_resolved = self.hybrid_router._is_rule_resolved(vector, rule_res)

            if not is_rule_resolved:
                # Attempt text-based deterministic classification before calling LLM
                text_decision = self.hybrid_router._classify_by_text_content(vector, rule_res)
                if text_decision:
                    llm_res = text_decision
                else:
                    # Use hybrid router for single message via process_batch
                    single_results = self.hybrid_router.process_batch(
                        vectors=[vector],
                        rule_results=[rule_res],
                        context=self.context,
                        media_results=[med_res] if med_res else None,
                        retrieval_results=[ret_res] if ret_res else None,
                    )
                    llm_res = single_results[0] if single_results else DecisionResult(
                        message_id=msg_id,
                        action="digest",
                        message_type="business_update",
                        reason="Multi-LLM routing completed with contextual signals.",
                        confidence=0.60,
                        provider="Rule Engine Fallback",
                        latency=0.0,
                    )
            else:
                llm_res = DecisionResult(
                    message_id=msg_id,
                    action=rule_res.action if rule_res.action != "unresolved" else "digest",
                    message_type=rule_res.message_type if rule_res.message_type not in ("unknown", "general", "") else "business_update",
                    reason=rule_res.reason,
                    confidence=rule_res.confidence if rule_res.confidence > 0 else 0.90,
                    provider="RuleEngine",
                    latency=0.0,
                )

            # Step 5: Decision Fusion
            return self.fusion_engine.fuse_decision(
                vector=vector,
                rule_result=rule_res,
                llm_result=llm_res,
                media_result=med_res,
                retrieval_result=ret_res,
                context=self.context,
            )
        except Exception as exc:
            logger.error(f"Error processing message '{msg_id}': {exc}. Triggering pipeline fallback.")
            return FinalDecision(
                message_id=msg_id,
                action="digest",
                message_type="business_update",
                reason="Unable to process message. Defaulted to business update.",
                confidence=0.50,
                evidence_message_ids=["none"],
                decision_source="FALLBACK",
                processing_time=0.0,
            )
