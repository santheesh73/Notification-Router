"""Image File Validator."""

from pathlib import Path


class ImageValidator:
    """Validates image file integrity, existence, and format."""

    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

    def validate_file(self, file_path: Path) -> bool:
        """Validate image file.

        Args:
            file_path: Path to image file.

        Returns:
            True if image file exists and is valid, else False.
        """
        if not file_path.exists() or not file_path.is_file():
            return False

        if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            return False

        if file_path.stat().st_size == 0:
            return False

        return True
