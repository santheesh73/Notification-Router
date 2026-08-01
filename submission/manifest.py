"""Submission Manifest Generator."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import PROJECT_ROOT


@dataclass
class ManifestData:
    """Dataclass encapsulating submission package manifest."""

    timestamp: str = ""
    included_files: list[str] = field(default_factory=list)
    total_files: int = 0
    total_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest data to dictionary."""
        return asdict(self)


class SubmissionManifest:
    """Generates package manifest metadata."""

    def build_manifest(self, file_paths: list[Path]) -> ManifestData:
        """Build ManifestData from list of file paths.

        Args:
            file_paths: List of absolute or relative Path objects included in submission zip.

        Returns:
            ManifestData object.
        """
        rel_paths: list[str] = []
        total_size = 0

        for p in file_paths:
            if p.exists() and p.is_file():
                try:
                    rel_p = str(p.relative_to(PROJECT_ROOT))
                except ValueError:
                    rel_p = p.name
                rel_paths.append(rel_p)
                total_size += p.stat().st_size

        return ManifestData(
            timestamp=datetime.now().isoformat(),
            included_files=rel_paths,
            total_files=len(rel_paths),
            total_bytes=total_size,
        )
