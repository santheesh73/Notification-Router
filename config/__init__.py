"""Configuration package for WhatsApp Notification Router."""

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
    Settings,
    settings,
)

__all__ = [
    "PROJECT_ROOT",
    "DATASET_PATH",
    "MEDIA_PATH",
    "IMAGE_PATH",
    "VOICE_PATH",
    "LOG_PATH",
    "OUTPUT_PATH",
    "CHECKPOINT_INTERVAL",
    "LOG_LEVEL",
    "Settings",
    "settings",
]
