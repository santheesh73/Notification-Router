"""Package Builder for Submission Zip Creation."""

import os
from pathlib import Path
import zipfile

from config.settings import PROJECT_ROOT
from submission.manifest import ManifestData, SubmissionManifest
from src.utils.logger import logger

EXCLUDE_DIRS: set[str] = {
    "dataset",
    "logs",
    "output",
    "reports",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "artifacts",
}

EXCLUDE_EXTENSIONS: set[str] = {".zip", ".pyc", ".pyo", ".pyd"}


class PackageBuilder:
    """Creates code.zip containing required codebase files for hackathon submission."""

    def __init__(self, zip_output_path: Path | None = None) -> None:
        """Initialize PackageBuilder.

        Args:
            zip_output_path: Path to target zip file. Defaults to PROJECT_ROOT/code.zip.
        """
        self.zip_path: Path = zip_output_path or (PROJECT_ROOT / "code.zip")
        self.manifest_builder: SubmissionManifest = SubmissionManifest()

    def build_package(self) -> tuple[Path, ManifestData]:
        """Build code.zip file excluding dataset, logs, output, and cache directories.

        Returns:
            Tuple of (Path_to_zip_file, ManifestData).
        """
        logger.info(f"Creating submission package at: {self.zip_path}")
        included_files: list[Path] = []

        with zipfile.ZipFile(self.zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(PROJECT_ROOT):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

                root_path = Path(root)

                for f_name in files:
                    f_path = root_path / f_name

                    # Skip excluded extensions or zip output itself
                    if f_path.suffix in EXCLUDE_EXTENSIONS or f_path == self.zip_path:
                        continue

                    rel_path = f_path.relative_to(PROJECT_ROOT)

                    # Ensure relative path doesn't start with excluded directory
                    first_part = rel_path.parts[0] if rel_path.parts else ""
                    if first_part in EXCLUDE_DIRS:
                        continue

                    zf.write(f_path, arcname=str(rel_path))
                    included_files.append(f_path)

        manifest = self.manifest_builder.build_manifest(included_files)
        logger.success(f"Successfully packaged {manifest.total_files} files into code.zip ({manifest.total_bytes / 1024:.1f} KB).")
        return self.zip_path, manifest
