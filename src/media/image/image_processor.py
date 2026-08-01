"""Image Processor with Vision AI Model Abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.media.image.image_parser import ImageParser
from src.media.image.image_validator import ImageValidator
from src.media.media_result import MediaResult
from src.utils.logger import logger


class BaseVisionModel(ABC):
    """Abstract interface for Vision AI models (GPT-4.5-VL, Qwen-VL)."""

    @abstractmethod
    def analyze(self, image_path: Path) -> dict[str, Any]:
        """Analyze image file and return structured dictionary of vision extraction.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary containing vision model extraction results.
        """
        pass


class MockVisionModel(BaseVisionModel):
    """Mock Vision AI model for deterministic testing and fallback processing."""

    def analyze(self, image_path: Path) -> dict[str, Any]:
        filename = image_path.name.lower()
        if "arch" in filename or "diagram" in filename:
            return {
                "classification": "Meeting Notice",
                "summary": "Architecture diagram for engineering review meeting.",
                "entities": ["architecture", "diagram", "meeting"],
                "dates": ["2026-08-05"],
                "times": ["10:00 AM"],
                "amounts": [],
                "people": ["Alice Smith", "Charlie Brown"],
                "organizations": ["DevOps Team"],
                "locations": ["Meeting Room A"],
                "urgency": "medium",
                "risk": "low",
                "confidence": 0.95,
            }
        elif "invoice" in filename or "receipt" in filename:
            return {
                "classification": "Invoice",
                "summary": "Billing invoice for recent cloud services subscription.",
                "entities": ["invoice", "billing", "payment"],
                "dates": ["2026-08-01"],
                "times": [],
                "amounts": ["$150.00"],
                "people": [],
                "organizations": ["Acme Logistics"],
                "locations": [],
                "urgency": "high",
                "risk": "low",
                "confidence": 0.92,
            }
        else:
            return {
                "classification": "Document",
                "summary": "Visual document image attachment.",
                "entities": ["document"],
                "dates": [],
                "times": [],
                "amounts": [],
                "people": [],
                "organizations": [],
                "locations": [],
                "urgency": "low",
                "risk": "low",
                "confidence": 0.88,
            }


class ImageProcessor:
    """Orchestrates image validation, vision model analysis, and normalization into MediaResult."""

    def __init__(self, vision_model: BaseVisionModel | None = None) -> None:
        """Initialize ImageProcessor.

        Args:
            vision_model: BaseVisionModel provider implementation. Defaults to MockVisionModel.
        """
        self.vision_model: BaseVisionModel = vision_model or MockVisionModel()
        self.validator: ImageValidator = ImageValidator()
        self.parser: ImageParser = ImageParser()

    def process_image(self, image_path: Path, message_id: str) -> MediaResult:
        """Process image file into MediaResult.

        Args:
            image_path: Path to image file.
            message_id: Message identifier string.

        Returns:
            Constructed MediaResult object.
        """
        if not self.validator.validate_file(image_path):
            logger.warning(f"Invalid or missing image file at: {image_path}")
            return MediaResult(
                message_id=message_id,
                media_type="image",
                processed=False,
                summary="Invalid or missing image file.",
                classification="Unknown",
                confidence=0.0,
            )

        try:
            raw_analysis = self.vision_model.analyze(image_path)
            parsed_data = self.parser.parse(raw_analysis)

            result = MediaResult(
                message_id=message_id,
                media_type="image",
                processed=True,
                summary=parsed_data["summary"],
                classification=parsed_data["classification"],
                entities=parsed_data["entities"],
                dates=parsed_data["dates"],
                times=parsed_data["times"],
                amounts=parsed_data["amounts"],
                people=parsed_data["people"],
                organizations=parsed_data["organizations"],
                locations=parsed_data["locations"],
                urgency=parsed_data["urgency"],
                risk=parsed_data["risk"],
                confidence=parsed_data["confidence"],
                raw_output=parsed_data["raw_output"],
            )
            logger.success(f"Processed image '{image_path.name}' -> [{result.classification}]")
            return result
        except Exception as exc:
            logger.error(f"Error processing image '{image_path}': {exc}")
            return MediaResult(
                message_id=message_id,
                media_type="image",
                processed=False,
                summary=f"Processing error: {exc}",
                classification="Unknown",
                confidence=0.0,
            )
