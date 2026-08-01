"""Multimodal Media Pipeline & Batch Processor."""

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd
from tabulate import tabulate

from src.media.media_manager import MediaManager
from src.media.media_result import MediaResult
from src.utils.logger import logger


@dataclass
class MediaValidationReport:
    """Dataclass holding validation report for media understanding outputs."""

    missing_message_ids: list[str] = field(default_factory=list)
    unprocessed_media: list[str] = field(default_factory=list)
    invalid_confidences: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors are found."""
        return len(self.missing_message_ids) == 0 and len(self.invalid_confidences) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class MediaPipeline:
    """Batch orchestrator for multimodal image and voice understanding."""

    def __init__(self, manager: MediaManager | None = None) -> None:
        """Initialize MediaPipeline.

        Args:
            manager: MediaManager instance.
        """
        self.manager: MediaManager = manager or MediaManager()

    def process_batch(self, messages_df: pd.DataFrame, repository: Any | None = None) -> list[MediaResult]:
        """Process a dataframe of messages into MediaResults.

        Args:
            messages_df: pandas DataFrame containing message records.
            repository: Optional DataRepository instance.

        Returns:
            List of MediaResult objects.
        """
        if repository and hasattr(self.manager, "load_repository_mappings"):
            self.manager.load_repository_mappings(repository)

        logger.info(f"Processing media understanding for {len(messages_df)} messages...")
        results: list[MediaResult] = []
        for _, row in messages_df.iterrows():
            res = self.manager.process_media(row.to_dict(), repository=repository)
            results.append(res)
        logger.success(f"Successfully processed {len(results)} media results.")
        return results

    def validate(self, results: list[MediaResult]) -> MediaValidationReport:
        """Validate MediaResult outputs.

        Args:
            results: List of MediaResult instances.

        Returns:
            MediaValidationReport object.
        """
        report = MediaValidationReport()

        for res in results:
            if not res.message_id:
                report.missing_message_ids.append(res.message_id)

            if res.media_type != "none" and not res.processed:
                report.unprocessed_media.append(res.message_id)

            if res.confidence < 0.0 or res.confidence > 1.0:
                report.invalid_confidences.append(f"{res.message_id}: {res.confidence}")

        logger.info(f"Media validation completed. Is valid: {report.is_valid}")
        return report

    def summary(self, results: list[MediaResult]) -> str:
        """Generate statistical summary report across media processing results.

        Args:
            results: List of MediaResult instances.

        Returns:
            Formatted ASCII summary table string.
        """
        if not results:
            return "No MediaResults available for summary."

        total_m = len(results)
        img_results = [r for r in results if r.media_type == "image"]
        voice_results = [r for r in results if r.media_type == "voice"]
        non_media_cnt = sum(1 for r in results if r.media_type == "none")

        avg_ocr_conf = sum(r.confidence for r in img_results) / len(img_results) if img_results else 0.0
        avg_trans_conf = sum(r.confidence for r in voice_results) / len(voice_results) if voice_results else 0.0

        # Classifications distribution
        class_counts: dict[str, int] = {}
        for r in results:
            if r.processed and r.classification != "None":
                class_counts[r.classification] = class_counts.get(r.classification, 0) + 1

        rows = [
            ["Total Messages Evaluated", total_m],
            ["Images Processed", len(img_results)],
            ["Voice Notes Processed", len(voice_results)],
            ["Non-Media Messages", non_media_cnt],
            ["Average OCR Confidence", f"{avg_ocr_conf:.4f}"],
            ["Average Transcription Confidence", f"{avg_trans_conf:.4f}"],
            ["Cache Hit Rate", f"{self.manager.cache.hit_rate * 100:.1f}%"],
            ["Detected Classifications", ", ".join([f"{k}:{v}" for k, v in class_counts.items()]) if class_counts else "None"],
        ]

        return tabulate(rows, headers=["Multimodal Metric", "Statistical Value"], tablefmt="grid")
