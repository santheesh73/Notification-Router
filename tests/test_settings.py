"""Unit tests for configuration settings."""

from pathlib import Path

from config.settings import (
    CHECKPOINT_INTERVAL,
    DATASET_PATH,
    IMAGE_PATH,
    LOG_LEVEL,
    LOG_PATH,
    MEDIA_PATH,
    OUTPUT_PATH,
    PROJECT_ROOT,
    VOICE_PATH,
    settings,
)


def test_project_root_exists() -> None:
    """Verify PROJECT_ROOT is resolved correctly as a directory."""
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_relative_paths() -> None:
    """Verify child path configurations are properly derived from PROJECT_ROOT."""
    assert DATASET_PATH == PROJECT_ROOT / "dataset"
    assert MEDIA_PATH == DATASET_PATH / "media"
    assert IMAGE_PATH == MEDIA_PATH / "images"
    assert VOICE_PATH == MEDIA_PATH / "audio"
    assert LOG_PATH == PROJECT_ROOT / "logs"
    assert OUTPUT_PATH == PROJECT_ROOT / "output"


def test_settings_dataclass() -> None:
    """Verify settings singleton instance attributes match module constants."""
    assert settings.project_root == PROJECT_ROOT
    assert settings.dataset_path == DATASET_PATH
    assert settings.media_path == MEDIA_PATH
    assert settings.image_path == IMAGE_PATH
    assert settings.voice_path == VOICE_PATH
    assert settings.log_path == LOG_PATH
    assert settings.output_path == OUTPUT_PATH
    assert settings.checkpoint_interval == CHECKPOINT_INTERVAL
    assert settings.log_level == LOG_LEVEL
