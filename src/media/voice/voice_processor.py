"""Voice Processor with Speech AI Model Abstraction."""

from pathlib import Path

from src.media.media_result import MediaResult
from src.media.voice.transcript_parser import TranscriptParser
from src.media.voice.transcript_validator import TranscriptValidator
from src.media.voice.transcription import BaseAudioModel, MockAudioModel
from src.utils.logger import logger


class VoiceProcessor:
    """Orchestrates audio validation, speech-to-text transcription, and normalization into MediaResult."""

    def __init__(self, audio_model: BaseAudioModel | None = None) -> None:
        """Initialize VoiceProcessor.

        Args:
            audio_model: BaseAudioModel provider implementation. Defaults to MockAudioModel.
        """
        self.audio_model: BaseAudioModel = audio_model or MockAudioModel()
        self.validator: TranscriptValidator = TranscriptValidator()
        self.parser: TranscriptParser = TranscriptParser()

    def process_voice(self, audio_path: Path, message_id: str) -> MediaResult:
        """Process voice note audio file into MediaResult.

        Args:
            audio_path: Path to audio file.
            message_id: Message identifier string.

        Returns:
            Constructed MediaResult object.
        """
        if not self.validator.validate_file(audio_path):
            logger.warning(f"Invalid or missing audio file at: {audio_path}")
            return MediaResult(
                message_id=message_id,
                media_type="voice",
                processed=False,
                summary="Invalid or missing audio file.",
                classification="Unknown",
                confidence=0.0,
            )

        try:
            raw_transcript = self.audio_model.transcribe(audio_path)
            parsed_data = self.parser.parse(raw_transcript)

            result = MediaResult(
                message_id=message_id,
                media_type="voice",
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
            logger.success(f"Processed voice note '{audio_path.name}' -> [{result.classification}]")
            return result
        except Exception as exc:
            logger.error(f"Error processing voice note '{audio_path}': {exc}")
            return MediaResult(
                message_id=message_id,
                media_type="voice",
                processed=False,
                summary=f"Transcription error: {exc}",
                classification="Unknown",
                confidence=0.0,
            )
