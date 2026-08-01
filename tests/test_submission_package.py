"""Unit tests for PackageBuilder and SubmissionVerifier."""

from pathlib import Path
import zipfile

from submission.package import PackageBuilder
from submission.verifier import SubmissionVerifier


def test_package_builder_and_verifier(tmp_path: Path) -> None:
    """Test building code.zip package and running submission verifier."""
    zip_target = tmp_path / "code.zip"
    builder = PackageBuilder(zip_output_path=zip_target)

    zip_file, manifest = builder.build_package()

    assert zip_file.exists()
    assert zip_file.stat().st_size > 0
    assert manifest.total_files > 0

    with zipfile.ZipFile(zip_file, "r") as zf:
        file_list = zf.namelist()
        assert any(f.startswith("src/") for f in file_list)
        assert any(f.startswith("config/") for f in file_list)
        assert "main.py" in file_list
        assert not any(f.startswith("dataset/") for f in file_list)
