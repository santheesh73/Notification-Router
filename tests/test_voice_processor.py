"""Unit tests for VoiceProcessor and speech models."""

from pathlib import Path

from config.settings import VOICE_PATH
from src.media.media_result import MediaResult
from src.media.voice.voice_processor import MockAudioModel, VoiceProcessor


def test_voice_processor_valid_audio(tmp_path: Path) -> None:
    """Test VoiceProcessor on existing voice note file."""
    processor = VoiceProcessor(audio_model=MockAudioModel())
    audio_file = tmp_path / "sample_voice.wav"
    audio_file.write_bytes(b"dummy audio bytes")

    res = processor.process_voice(audio_file, message_id="MSG_VOICE_TEST")

    assert isinstance(res, MediaResult)
    assert res.message_id == "MSG_VOICE_TEST"
    assert res.media_type == "voice"
    assert res.processed is True
    assert res.classification in ["Meeting", "Action Request", "Reminder", "Payment"]


def test_voice_processor_missing_audio() -> None:
    """Test VoiceProcessor handling missing audio file."""
    processor = VoiceProcessor()
    missing_file = Path("non_existent_audio.wav")

    res = processor.process_voice(missing_file, message_id="MSG_MISSING_AUDIO")

    assert res.processed is False
    assert res.classification == "Unknown"
