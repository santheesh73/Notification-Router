"""Runtime Configuration, Centralized Statistics, and Execution Context.

Centralizes runtime options (CLI args), execution metrics (Rule Coverage, LLM Coverage),
and provides automatic consistency verification across reports.
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.settings import DATASET_PATH, OUTPUT_CSV_PATH, PROJECT_ROOT
from src.utils.logger import logger


@dataclass
class RuntimeConfig:
    """Dataclass encapsulating CLI arguments and dynamic runtime paths."""

    input_path: Path = field(default_factory=lambda: DATASET_PATH / "messages.csv")
    output_path: Path = field(default_factory=lambda: OUTPUT_CSV_PATH)
    dataset_path: Path = field(default_factory=lambda: DATASET_PATH)
    batch_size: int = 50
    checkpoint_interval: int = 25
    resume: bool = True
    overwrite_output: bool = True

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace | None = None) -> "RuntimeConfig":
        """Build RuntimeConfig from CLI arguments or sys.argv with fallback to defaults.

        Supports:
            --input / -i: Path to input messages CSV file.
            --output / -o: Path to target output CSV file.
            --dataset / -d: Directory path containing dataset CSV files.
        """
        if args is None:
            parser = argparse.ArgumentParser(
                description="AI-powered WhatsApp Notification Router with Hybrid Multi-LLM Routing"
            )
            parser.add_argument("--input", "-i", type=str, default=None, help="Path to input messages CSV file")
            parser.add_argument("--output", "-o", type=str, default=None, help="Path to target output CSV file")
            parser.add_argument("--dataset", "-d", type=str, default=None, help="Directory path for datasets")
            args, _ = parser.parse_known_args()

        # 1. Resolve dataset_path
        if getattr(args, "dataset", None):
            dataset_p = Path(args.dataset)
            if not dataset_p.is_absolute():
                dataset_p = (PROJECT_ROOT / dataset_p).resolve()
        else:
            dataset_p = DATASET_PATH

        # 2. Resolve input_path
        if getattr(args, "input", None):
            inp_p = Path(args.input)
            if not inp_p.is_absolute():
                inp_p = (PROJECT_ROOT / inp_p).resolve()
        else:
            inp_p = (dataset_p / "messages.csv").resolve()

        # 3. Resolve output_path
        if getattr(args, "output", None):
            out_p = Path(args.output)
            if not out_p.is_absolute():
                out_p = (PROJECT_ROOT / out_p).resolve()
        else:
            out_p = OUTPUT_CSV_PATH.resolve()

        return cls(
            input_path=inp_p,
            output_path=out_p,
            dataset_path=dataset_p,
        )


@dataclass
class RuntimeStatistics:
    """Central store for runtime execution statistics and metrics."""

    total_messages: int = 0
    images_count: int = 0
    voice_count: int = 0
    rule_resolved_count: int = 0
    llm_resolved_count: int = 0
    fallback_count: int = 0
    rule_coverage_pct: float = 0.0
    llm_coverage_pct: float = 0.0
    action_counts: dict[str, int] = field(default_factory=dict)
    type_counts: dict[str, int] = field(default_factory=dict)
    confidence_min: float = 0.0
    confidence_mean: float = 0.0
    confidence_max: float = 0.0
    evidence_usage_pct: float = 0.0
    cache_hit_rate: float = 0.0

    def compute_from_decisions(self, decisions: list[Any]) -> None:
        """Compute all runtime statistics ONCE from final decisions list."""
        self.total_messages = len(decisions)
        if self.total_messages == 0:
            self.rule_coverage_pct = 0.0
            self.llm_coverage_pct = 0.0
            return

        rule_cnt = 0
        llm_cnt = 0
        fallback_cnt = 0

        for d in decisions:
            is_ai = getattr(d, "resolved_by_ai", False)
            source = str(getattr(d, "decision_source", ""))

            if is_ai or "LLM" in source:
                llm_cnt += 1
            elif source == "FALLBACK":
                fallback_cnt += 1
            else:
                rule_cnt += 1

        self.rule_resolved_count = rule_cnt
        self.llm_resolved_count = llm_cnt
        self.fallback_count = fallback_cnt

        self.rule_coverage_pct = round((rule_cnt / self.total_messages) * 100.0, 1)
        self.llm_coverage_pct = round((llm_cnt / self.total_messages) * 100.0, 1)

        self.action_counts = {}
        self.type_counts = {}
        ev_count = 0
        conf_vals = []

        for d in decisions:
            act = str(getattr(d, "action", ""))
            mtype = str(getattr(d, "message_type", ""))
            conf = float(getattr(d, "confidence", 0.0))
            ev_ids = getattr(d, "evidence_message_ids", [])

            self.action_counts[act] = self.action_counts.get(act, 0) + 1
            self.type_counts[mtype] = self.type_counts.get(mtype, 0) + 1
            conf_vals.append(conf)

            if ev_ids and ev_ids != ["none"] and len(ev_ids) > 0:
                ev_count += 1

        self.confidence_min = min(conf_vals) if conf_vals else 0.0
        self.confidence_max = max(conf_vals) if conf_vals else 0.0
        self.confidence_mean = (sum(conf_vals) / len(conf_vals)) if conf_vals else 0.0
        self.evidence_usage_pct = round((ev_count / self.total_messages) * 100.0, 1)

    def verify_consistency(self, reported_rule_coverage: float, reported_llm_coverage: float) -> None:
        """Verify report consistency and raise RuntimeError if coverage metrics differ."""
        if abs(reported_rule_coverage - self.rule_coverage_pct) > 0.1:
            msg = (
                f"Consistency Error: Rule Coverage mismatch detected across reports! "
                f"Stored={self.rule_coverage_pct}%, Reported={reported_rule_coverage}%"
            )
            logger.error(msg)
            raise RuntimeError(msg)

        if abs(reported_llm_coverage - self.llm_coverage_pct) > 0.1:
            msg = (
                f"Consistency Error: LLM Coverage mismatch detected across reports! "
                f"Stored={self.llm_coverage_pct}%, Reported={reported_llm_coverage}%"
            )
            logger.error(msg)
            raise RuntimeError(msg)


class ExecutionContext:
    """Global or instance execution context wrapping RuntimeConfig and RuntimeStatistics."""

    _instance: "ExecutionContext | None" = None

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config: RuntimeConfig = config or RuntimeConfig()
        self.stats: RuntimeStatistics = RuntimeStatistics()
        ExecutionContext._instance = self

    @classmethod
    def get_current(cls) -> "ExecutionContext":
        """Get or initialize singleton ExecutionContext instance."""
        if cls._instance is None:
            cls._instance = ExecutionContext()
        return cls._instance
