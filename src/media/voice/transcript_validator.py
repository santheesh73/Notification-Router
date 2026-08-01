"""Audio & Transcript Validator."""

from pathlib import Path


class TranscriptValidator:
    """Validates audio file integrity, audio formats, and transcript validity."""

    ALLOWED_EXTENSIONS: set[str] = {".wav", ".mp3", ".ogg", ".m4a", ".aac", ".flac", ".opus"}

    def validate_file(self, file_path: Path) -> bool:
        """Validate audio file.

        Args:
            file_path: Path to audio file.

        Returns:
            True if audio file exists and is valid, else False.
        """
        if not file_path.exists() or not file_path.is_file():
            return False

        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            return False

        if file_path.stat().st_size == 0:
            return False

        return True
