"""Unit tests for Singleton Logger Utility."""

from pathlib import Path
import tempfile

from src.utils.logger import get_logger, logger, setup_logger


def test_logger_instance() -> None:
    """Test logger initialization and method access."""
    log_inst = get_logger()
    assert log_inst is not None
    assert log_inst == logger


def test_custom_logger_setup() -> None:
    """Test setting up logger with custom directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        custom_log = setup_logger(log_dir=tmp_path, log_level="DEBUG")

        custom_log.info("Testing custom logger output")
        custom_log.warning("Testing warning message")
        custom_log.error("Testing error message")

        # Flush enqueued messages and release Windows file handle
        custom_log.remove()

        log_file = tmp_path / "app.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Testing custom logger output" in content
        assert "Testing warning message" in content
        assert "Testing error message" in content


