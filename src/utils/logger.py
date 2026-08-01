"""Singleton Logger Utility using Loguru.

Provides structured, colored console logging and persistent file logging
to logs/app.log with support for INFO, WARNING, ERROR, SUCCESS, and DEBUG levels.
"""

from pathlib import Path
import sys
from typing import Any

from loguru import logger as _loguru_logger

from config.settings import LOG_LEVEL, LOG_PATH


def setup_logger(
    log_dir: Path | None = None,
    log_level: str | None = None,
) -> Any:
    """Configure Loguru logger with console and file handlers.

    Args:
        log_dir: Target directory for log files. Defaults to LOG_PATH from settings.
        log_level: Severity threshold (DEBUG, INFO, WARNING, ERROR, SUCCESS).

    Returns:
        Configured Loguru logger instance.
    """
    target_log_dir = log_dir or LOG_PATH
    target_log_level = log_level or LOG_LEVEL

    # Ensure log directory exists
    target_log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = target_log_dir / "app.log"

    # Remove standard default handlers
    _loguru_logger.remove()

    # Console Handler (Colored)
    _loguru_logger.add(
        sys.stdout,
        level=target_log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # File Handler
    _loguru_logger.add(
        str(log_file_path),
        level=target_log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    return _loguru_logger


# Singleton logger instance initialized on import
logger = setup_logger()


def get_logger() -> Any:
    """Get the initialized logger instance.

    Returns:
        Loguru logger instance.
    """
    return logger
