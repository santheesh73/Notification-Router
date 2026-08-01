"""Central Configuration Settings for WhatsApp Message Notification Router.

All paths are computed dynamically relative to PROJECT_ROOT to eliminate
hardcoded absolute path dependencies. Settings can be overridden using
environment variables or a .env file.
"""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# Dynamic project root resolution: two directory levels up from config/settings.py
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Base directory paths derived from PROJECT_ROOT
DATASET_PATH: Path = Path(os.getenv("DATASET_PATH", PROJECT_ROOT / "dataset"))
MEDIA_PATH: Path = Path(os.getenv("MEDIA_PATH", DATASET_PATH / "media"))
IMAGE_PATH: Path = Path(os.getenv("IMAGE_PATH", MEDIA_PATH / "images"))
VOICE_PATH: Path = Path(os.getenv("VOICE_PATH", MEDIA_PATH / "audio"))
LOG_PATH: Path = Path(os.getenv("LOG_PATH", PROJECT_ROOT / "logs"))
LOGS_PATH: Path = LOG_PATH
OUTPUT_PATH: Path = Path(os.getenv("OUTPUT_PATH", PROJECT_ROOT / "output"))
OUTPUT_CSV_PATH: Path = Path(os.getenv("OUTPUT_CSV_PATH", OUTPUT_PATH / "output.csv"))

# Execution & Routing Configuration
CHECKPOINT_INTERVAL: int = int(os.getenv("CHECKPOINT_INTERVAL", "100"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


@dataclass(frozen=True)
class Settings:
    """Dataclass holding all system configuration options."""

    project_root: Path = PROJECT_ROOT
    dataset_path: Path = DATASET_PATH
    media_path: Path = MEDIA_PATH
    image_path: Path = IMAGE_PATH
    voice_path: Path = VOICE_PATH
    log_path: Path = LOG_PATH
    output_path: Path = OUTPUT_PATH
    checkpoint_interval: int = CHECKPOINT_INTERVAL
    log_level: str = LOG_LEVEL

    def ensure_directories_exist(self) -> None:
        """Create required system directories if they do not exist."""
        for path in [
            self.dataset_path,
            self.media_path,
            self.image_path,
            self.voice_path,
            self.log_path,
            self.output_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)


# Global settings singleton instance
settings = Settings()
