"""Unit tests for ImageProcessor and vision models."""

from pathlib import Path

from config.settings import IMAGE_PATH
from src.media.image.image_processor import ImageProcessor, MockVisionModel
from src.media.media_result import MediaResult


def test_image_processor_valid_image(tmp_path: Path) -> None:
    """Test ImageProcessor on existing image file."""
    processor = ImageProcessor(vision_model=MockVisionModel())
    img_file = tmp_path / "sample_arch.png"
    img_file.write_bytes(b"dummy image bytes")

    res = processor.process_image(img_file, message_id="MSG_IMG_TEST")

    assert isinstance(res, MediaResult)
    assert res.message_id == "MSG_IMG_TEST"
    assert res.media_type == "image"
    assert res.processed is True
    assert res.classification in ["Meeting Notice", "Invoice", "Document"]


def test_image_processor_missing_image() -> None:
    """Test ImageProcessor handling missing image file."""
    processor = ImageProcessor()
    missing_file = Path("non_existent_image.png")

    res = processor.process_image(missing_file, message_id="MSG_MISSING")

    assert res.processed is False
    assert res.classification == "Unknown"
