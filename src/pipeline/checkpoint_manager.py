"""Checkpoint Manager for Crash-Safe Execution Resumption."""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from config.settings import LOGS_PATH
from src.confidence.final_decision import FinalDecision
from src.utils.logger import logger


class CheckpointManager:
    """Manages execution state checkpoints for automatic resumption after system restarts."""

    def __init__(
        self,
        checkpoint_path: Path | None = None,
        interval: int = 25,
    ) -> None:
        """Initialize CheckpointManager.

        Args:
            checkpoint_path: Path to checkpoint JSON file. Defaults to logs/checkpoint.json.
            interval: Checkpoint save interval in message count (default 25).
        """
        self.checkpoint_path: Path = checkpoint_path or (LOGS_PATH / "checkpoint.json")
        self.interval: int = interval
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure parent directory exists."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        last_processed_index: int,
        processed_items: list[Any] | None = None,
        processed_ids: list[Any] | None = None,
    ) -> None:
        processed_items = processed_items if processed_items is not None else (processed_ids or [])
        """Save execution checkpoint state to JSON file.

        Args:
            last_processed_index: 0-indexed integer of last processed row.
            processed_items: List of processed FinalDecision instances or message IDs.
        """
        dec_dicts = []
        msg_ids = []

        for item in processed_items:
            if isinstance(item, str):
                msg_ids.append(item)
            elif isinstance(item, FinalDecision):
                dec_dicts.append(asdict(item))
                msg_ids.append(item.message_id)
            elif isinstance(item, dict):
                dec_dicts.append(item)
                if "message_id" in item:
                    msg_ids.append(item["message_id"])

        data = {
            "last_processed_index": last_processed_index,
            "processed_count": max(len(dec_dicts), len(msg_ids)),
            "processed_decisions": dec_dicts,
            "processed_message_ids": msg_ids,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            with open(self.checkpoint_path, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved checkpoint at index {last_processed_index} ({len(msg_ids)} messages processed).")
        except Exception as exc:
            logger.error(f"Failed to save checkpoint: {exc}")

    def load_checkpoint(self) -> tuple[int, Any]:
        """Load execution checkpoint state.

        Returns:
            Tuple of (last_processed_index, list_of_decisions_or_set_of_ids).
        """
        if not self.checkpoint_path.exists():
            return -1, set()

        try:
            with open(self.checkpoint_path, mode="r", encoding="utf-8") as f:
                data = json.load(f)

            last_idx = int(data.get("last_processed_index", -1))
            proc_ids = data.get("processed_message_ids", [])
            raw_decs = data.get("processed_decisions", [])

            if raw_decs:
                decisions: list[FinalDecision] = []
                for d in raw_decs:
                    if isinstance(d, dict):
                        decisions.append(
                            FinalDecision(
                                message_id=d.get("message_id", ""),
                                action=d.get("action", "digest"),
                                message_type=d.get("message_type", "unknown"),
                                reason=d.get("reason", ""),
                                confidence=float(d.get("confidence", 0.5)),
                                evidence_message_ids=d.get("evidence_message_ids", []),
                                decision_source=d.get("decision_source", "RULE_ENGINE"),
                                rule_used=d.get("rule_used", "None"),
                                llm_provider=d.get("llm_provider", "None"),
                                resolved_by_ai=bool(d.get("resolved_by_ai", False)),
                                processing_time=float(d.get("processing_time", 0.0)),
                            )
                        )
                logger.info(f"Loaded checkpoint at index {last_idx} with {len(decisions)} previous messages.")
                return last_idx, decisions
            else:
                proc_set = set(proc_ids)
                logger.info(f"Loaded checkpoint at index {last_idx} with {len(proc_set)} previous message IDs.")
                return last_idx, proc_set
        except Exception as exc:
            logger.error(f"Failed to load checkpoint ({exc}). Starting from beginning.")
            return -1, set()

    def clear_checkpoint(self) -> None:
        """Remove checkpoint file upon successful pipeline completion."""
        if self.checkpoint_path.exists():
            try:
                self.checkpoint_path.unlink()
                logger.info("Cleared execution checkpoint file.")
            except Exception as exc:
                logger.warning(f"Unable to clear checkpoint file: {exc}")
