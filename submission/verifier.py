"""Submission Verifier."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from config.settings import OUTPUT_CSV_PATH, PROJECT_ROOT
from src.utils.logger import logger

REQUIRED_FILES: list[Path] = [
    PROJECT_ROOT / "code.zip",
    OUTPUT_CSV_PATH,
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "requirements.txt",
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "chat_transcript.md",
    PROJECT_ROOT / "reports" / "execution_report.json",
    PROJECT_ROOT / "reports" / "benchmark_report.json",
    PROJECT_ROOT / "reports" / "quality_report.json",
    PROJECT_ROOT / "reports" / "summary.md",
]


@dataclass
class VerificationReport:
    """Dataclass holding submission package verification status."""

    missing_files: list[str] = field(default_factory=list)
    empty_files: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return True if no missing or empty files exist."""
        return len(self.missing_files) == 0 and len(self.empty_files) == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


class SubmissionVerifier:
    """Verifies that all required hackathon submission files exist and are valid."""

    def verify_submission(self) -> VerificationReport:
        """Verify presence and validity of code.zip, output.csv, README.md, requirements.txt, main.py, and reports.

        Returns:
            VerificationReport instance.
        """
        logger.info("Verifying hackathon submission deliverables...")
        report = VerificationReport()

        for req_file in REQUIRED_FILES:
            if not req_file.exists():
                report.missing_files.append(str(req_file.name))
                logger.error(f"Submission Verifier: Missing required deliverable file '{req_file.name}'!")
            elif req_file.stat().st_size == 0:
                report.empty_files.append(str(req_file.name))
                logger.error(f"Submission Verifier: Required file '{req_file.name}' is empty (0 bytes)!")

        if not report.is_valid:
            logger.error(f"Submission Verification FAILED: Missing={report.missing_files}, Empty={report.empty_files}")
        else:
            logger.success("Submission Verification PASSED: All deliverables verified successfully.")

        return report
