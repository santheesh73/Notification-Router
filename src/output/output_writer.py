"""CSV Output Writer with pre/post-validation and complete file overwriting."""

import csv
from pathlib import Path
from typing import Any

from config.settings import OUTPUT_CSV_PATH
from src.confidence.final_decision import FinalDecision
from src.output.csv_formatter import CSVFormatter
from src.utils.logger import logger


class OutputWriter:
    """Manages writing and validating predictions to output.csv."""

    def __init__(self, output_path: Path | None = None) -> None:
        """Initialize OutputWriter.

        Args:
            output_path: Target output CSV file path. Defaults to OUTPUT_CSV_PATH.
        """
        self.output_path: Path = output_path or OUTPUT_CSV_PATH
        self.formatter: CSVFormatter = CSVFormatter()
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure target parent directory exists."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def remove_old_output(self) -> None:
        """Check if output.csv exists and delete it before fresh execution."""
        if self.output_path.exists():
            try:
                self.output_path.unlink()
                logger.info("Old output removed")
                print("Old output removed")
            except Exception as exc:
                logger.warning(f"Could not remove old output.csv ({exc}). Overwriting instead.")

    def write_header(self, overwrite: bool = True) -> None:
        """Write CSV header in write mode ('w').

        Args:
            overwrite: Always set to True to write header in mode='w'.
        """
        self._ensure_output_dir()
        with open(self.output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSVFormatter.COLUMNS)
            writer.writeheader()
        logger.info(f"Initialized output CSV with header at: {self.output_path}")

    def write_all(self, decisions: list[FinalDecision], expected_count: int | None = None) -> None:
        """Pre-validate, remove old file, write all predictions in mode='w', and post-validate.

        Args:
            decisions: List of FinalDecision instances to write.
            expected_count: Optional expected row count to verify before writing.
        """
        # 1. Pre-validation: Verify length
        if expected_count is not None and len(decisions) != expected_count:
            logger.error(f"Row count mismatch: len(predictions)={len(decisions)} != expected={expected_count}")
            raise ValueError(f"Row count mismatch: {len(decisions)} predictions != {expected_count} expected")

        # 2. Remove old output
        self.remove_old_output()

        num_predictions = len(decisions)
        logger.info(f"Writing {num_predictions} predictions")
        print(f"Writing {num_predictions} predictions")

        # 3. Write predictions in write mode ('w') - NEVER append ('a')
        self._ensure_output_dir()
        with open(self.output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSVFormatter.COLUMNS)
            writer.writeheader()
            for dec in decisions:
                row_dict = self.formatter.format_decision(dec)
                writer.writerow(row_dict)
            f.flush()

        # 4. Post Validation: Immediately reload and verify
        self.validate_output_file(expected_count=expected_count or num_predictions)

    def validate_output_file(self, expected_count: int) -> bool:
        """Immediately reload output.csv and post-validate rows and columns.

        Args:
            expected_count: Expected row count integer.

        Returns:
            True if valid, else raises ValueError.
        """
        if not self.output_path.exists():
            logger.error("Post Validation Failed: output.csv does not exist.")
            raise ValueError("Output CSV validation failed: File missing")

        reloaded_rows: list[dict[str, str]] = []
        with open(self.output_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Check Columns
            fieldnames = reader.fieldnames or []
            for col in CSVFormatter.COLUMNS:
                if col not in fieldnames:
                    logger.error(f"Missing column in output.csv: {col}")
                    raise ValueError(f"Output CSV missing column: {col}")

            for row in reader:
                reloaded_rows.append(row)

        found_count = len(reloaded_rows)
        if found_count != expected_count:
            logger.error(f"Output CSV row count mismatch: found {found_count}, expected {expected_count}")
            raise ValueError(f"Output CSV row count mismatch: found {found_count}, expected {expected_count}")

        logger.info("Output CSV Validation PASSED")
        logger.info(f"Rows Found: {found_count}")
        logger.info(f"Expected: {expected_count}")
        logger.info("Output Schema Status: PASSED")
        logger.info("Validation Passed")
        logger.info(f"Rows Written: {found_count}")

        print("Output CSV Validation PASSED")
        print(f"Rows Found: {found_count}")
        print(f"Expected: {expected_count}")
        print("Output Schema Status: PASSED")
        print("Validation Passed")
        print(f"Rows Written: {found_count}")

        return True

    def write_row(self, decision: FinalDecision) -> None:
        """Write single FinalDecision row incrementally."""
        self._ensure_output_dir()
        file_exists = self.output_path.exists() and self.output_path.stat().st_size > 0
        mode = "a" if file_exists else "w"
        with open(self.output_path, mode=mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSVFormatter.COLUMNS)
            if not file_exists:
                writer.writeheader()
            row_dict = self.formatter.format_decision(decision)
            writer.writerow(row_dict)

    def write_batch(self, decisions: list[FinalDecision], overwrite: bool = True) -> None:
        """Write a batch of FinalDecisions to CSV."""
        self.write_all(decisions)
