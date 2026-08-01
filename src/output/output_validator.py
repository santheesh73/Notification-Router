"""CSV Output File Validator."""

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.output.csv_formatter import CSVFormatter
from src.utils.logger import logger

VALID_ACTIONS: set[str] = {"notify", "digest", "mute"}
VALID_MESSAGE_TYPES: set[str] = {
    "personal",
    "urgent",
    "event",
    "payment",
    "business",
    "business_update",
    "promotion",
    "greeting",
    "forward",
    "spam",
    "scam",
    "muted_group",
    "duplicate",
    "unknown",
    "office",
    "family",
    "group",
    "general",
    "social",
    "otp",
    "verification",
}


@dataclass
class OutputValidationReport:
    """Dataclass holding validation report for output.csv file."""

    total_rows: int = 0
    missing_columns: list[str] = field(default_factory=list)
    duplicate_message_ids: list[str] = field(default_factory=list)
    invalid_actions: list[str] = field(default_factory=list)
    invalid_message_types: list[str] = field(default_factory=list)
    invalid_confidences: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors exist."""
        return (
            len(self.missing_columns) == 0
            and len(self.duplicate_message_ids) == 0
            and len(self.invalid_actions) == 0
            and len(self.invalid_message_types) == 0
            and len(self.invalid_confidences) == 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class OutputValidator:
    """Validates output.csv format, column schema, row counts, and data bounds."""

    def validate_csv(self, file_path: Path, expected_row_count: int | None = None) -> OutputValidationReport:
        """Validate output CSV file.

        Args:
            file_path: Path to output CSV file.
            expected_row_count: Optional expected row count to verify.

        Returns:
            OutputValidationReport object.
        """
        report = OutputValidationReport()
        if not file_path.exists() or file_path.stat().st_size == 0:
            report.missing_columns = CSVFormatter.COLUMNS
            return report

        seen_ids: set[str] = set()

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Check header columns
            fieldnames = reader.fieldnames or []
            for col in CSVFormatter.COLUMNS:
                if col not in fieldnames:
                    report.missing_columns.append(col)

            for i, row in enumerate(reader):
                report.total_rows += 1
                msg_id = row.get("message_id", "").strip()

                if not msg_id or msg_id in seen_ids:
                    report.duplicate_message_ids.append(f"Row {i+1}: {msg_id}")
                else:
                    seen_ids.add(msg_id)

                act = row.get("action", "").strip()
                if act not in VALID_ACTIONS:
                    report.invalid_actions.append(f"{msg_id}: {act}")

                m_type = row.get("message_type", "").strip()
                if m_type not in VALID_MESSAGE_TYPES:
                    report.invalid_message_types.append(f"{msg_id}: {m_type}")

                try:
                    conf = float(row.get("confidence", -1))
                    if conf < 0.0 or conf > 1.0:
                        report.invalid_confidences.append(f"{msg_id}: {conf}")
                except ValueError:
                    report.invalid_confidences.append(f"{msg_id}: invalid_float")

        if expected_row_count is not None and report.total_rows != expected_row_count:
            logger.warning(
                f"Output CSV row count mismatch: found {report.total_rows}, expected {expected_row_count}."
            )

        logger.info(f"CSV Validation completed for '{file_path.name}'. Is valid: {report.is_valid}")
        return report
