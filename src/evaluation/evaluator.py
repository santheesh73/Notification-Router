"""Output Evaluator for CSV Verification."""

import csv
from pathlib import Path

from src.output.output_validator import OutputValidationReport, OutputValidator


class OutputEvaluator:
    """Rigorously evaluates output.csv schema, data integrity, and evidence formatting."""

    def __init__(self) -> None:
        """Initialize OutputEvaluator."""
        self.validator: OutputValidator = OutputValidator()

    def evaluate(
        self,
        output_csv_path: Path,
        expected_count: int | None = None,
    ) -> OutputValidationReport:
        """Evaluate output CSV file.

        Args:
            output_csv_path: Path to output.csv.
            expected_count: Optional expected row count.

        Returns:
            OutputValidationReport instance.
        """
        return self.validator.validate_csv(file_path=output_csv_path, expected_row_count=expected_count)
