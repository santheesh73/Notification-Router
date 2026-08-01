"""Audio Transcription Model Abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseAudioModel(ABC):
    """Abstract interface for Speech-to-Text Audio models (Whisper, Azure Speech, OpenAI Audio)."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> dict[str, Any]:
        """Transcribe audio file and return transcription result dictionary.

        Args:
            audio_path: Path to audio file.

        Returns:
            Dictionary containing transcript text, duration, language, and confidence.
        """
        pass


class MockAudioModel(BaseAudioModel):
    """Mock Audio model for deterministic testing and fallback processing."""

    def transcribe(self, audio_path: Path) -> dict[str, Any]:
        filename = audio_path.name.lower()
        if "voice_note_1" in filename or "voice" in filename:
            return {
                "text": "Hi Evan, this is a voice note regarding our quarterly planning meeting tomorrow at 2 PM.",
                "language": "en",
                "duration_seconds": 14.5,
                "confidence": 0.94,
                "speaker_count": 1,
            }
        else:
            return {
                "text": "Audio message transcript recorded successfully.",
                "language": "en",
                "duration_seconds": 5.0,
                "confidence": 0.90,
                "speaker_count": 1,
            }
