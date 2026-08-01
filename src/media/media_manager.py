"""Central Media Manager with Cached CSV Repository Mappings."""

from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DATASET_PATH, IMAGE_PATH, PROJECT_ROOT, VOICE_PATH
from src.loaders.load_data import DataRepository
from src.media.image.image_processor import ImageProcessor
from src.media.media_cache import MediaCache
from src.media.media_result import MediaResult
from src.media.voice.voice_processor import VoiceProcessor
from src.utils.logger import logger

VALID_IMAGE_EXTS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
VALID_AUDIO_EXTS: set[str] = {".wav", ".mp3", ".ogg", ".m4a", ".aac"}


class MediaManager:
    """Central manager resolving and delegating processing to ImageProcessor or VoiceProcessor."""

    def __init__(
        self,
        image_processor: ImageProcessor | None = None,
        voice_processor: VoiceProcessor | None = None,
        cache: MediaCache | None = None,
        repository: DataRepository | None = None,
    ) -> None:
        """Initialize MediaManager.

        Args:
            image_processor: ImageProcessor instance.
            voice_processor: VoiceProcessor instance.
            cache: MediaCache instance.
            repository: DataRepository instance.
        """
        self.image_processor: ImageProcessor = image_processor or ImageProcessor()
        self.voice_processor: VoiceProcessor = voice_processor or VoiceProcessor()
        self.cache: MediaCache = cache or MediaCache()

        self.image_map: dict[str, str] = {}
        self.voice_map: dict[str, str] = {}
        self._mappings_loaded: bool = False

        if repository:
            self.load_repository_mappings(repository)

    def load_repository_mappings(self, repository: DataRepository | None = None) -> tuple[dict[str, str], dict[str, str]]:
        """Load and cache repository mappings from images.csv and voice_notes.csv datasets.

        Loads mappings ONLY ONCE to prevent redundant file I/O during execution.

        Args:
            repository: DataRepository instance or None.

        Returns:
            Tuple of (image_mapping, voice_mapping) dictionaries.
        """
        if self._mappings_loaded:
            return self.image_map, self.voice_map

        self.image_map.clear()
        self.voice_map.clear()

        repo = repository
        if repo is None:
            try:
                repo = DataRepository(dataset_path=DATASET_PATH)
                repo.load_all()
            except Exception as exc:
                logger.warning(f"MediaManager: Could not load repository directly ({exc}).")

        # 1. Load images.csv
        if repo:
            try:
                images_df = repo.get_dataframe("images")
                if not images_df.empty:
                    id_col = None
                    for col in ["image_id", "media_id", "message_id"]:
                        if col in images_df.columns:
                            id_col = col
                            break

                    if id_col and "file_path" in images_df.columns:
                        for _, row in images_df.iterrows():
                            img_id = str(row[id_col]).strip()
                            raw_path = str(row["file_path"]).strip()

                            if img_id in self.image_map:
                                logger.warning(f"Duplicate image media_id '{img_id}' detected in images.csv.")

                            abs_path = self._resolve_path(raw_path, IMAGE_PATH)

                            if not self._validate_media_file(abs_path, VALID_IMAGE_EXTS):
                                logger.warning(f"Missing, invalid, or corrupted image file for '{img_id}' at: {abs_path}")

                            self.image_map[img_id] = str(abs_path)
                            if "message_id" in row and pd.notna(row["message_id"]):
                                self.image_map[str(row["message_id"]).strip()] = str(abs_path)

                            logger.info(f"Mapped {img_id} -> {raw_path}")
            except Exception as exc:
                logger.warning(f"Error reading images.csv: {exc}")

        # 2. Load voice_notes.csv
        if repo:
            try:
                voice_df = repo.get_dataframe("voice_notes")
                if not voice_df.empty:
                    id_col = None
                    for col in ["voice_note_id", "media_id", "message_id"]:
                        if col in voice_df.columns:
                            id_col = col
                            break

                    if id_col and "file_path" in voice_df.columns:
                        for _, row in voice_df.iterrows():
                            v_id = str(row[id_col]).strip()
                            raw_path = str(row["file_path"]).strip()

                            if v_id in self.voice_map:
                                logger.warning(f"Duplicate voice media_id '{v_id}' detected in voice_notes.csv.")

                            abs_path = self._resolve_path(raw_path, VOICE_PATH)

                            if not self._validate_media_file(abs_path, VALID_AUDIO_EXTS):
                                logger.warning(f"Missing, invalid, or corrupted voice file for '{v_id}' at: {abs_path}")

                            self.voice_map[v_id] = str(abs_path)
                            if "message_id" in row and pd.notna(row["message_id"]):
                                self.voice_map[str(row["message_id"]).strip()] = str(abs_path)

                            logger.info(f"Mapped {v_id} -> {raw_path}")
            except Exception as exc:
                logger.warning(f"Error reading voice_notes.csv: {exc}")

        # Unique count calculation
        img_count = len(self.image_map)
        voice_count = len(self.voice_map)
        if repo:
            try:
                img_df = repo.get_dataframe("images")
                if not img_df.empty:
                    img_count = len(img_df)
            except Exception:
                pass

            try:
                vc_df = repo.get_dataframe("voice_notes")
                if not vc_df.empty:
                    voice_count = len(vc_df)
            except Exception:
                pass

        logger.info(f"Loaded {img_count} image mappings")
        logger.info(f"Loaded {voice_count} voice note mappings")

        self._mappings_loaded = True
        return self.image_map, self.voice_map

    def process_media(self, message: dict[str, Any], repository: DataRepository | None = None) -> MediaResult:
        """Process media message into MediaResult dynamically using cached repository mapping.

        Args:
            message: Message record dictionary.
            repository: Optional DataRepository instance.

        Returns:
            Constructed MediaResult instance.
        """
        if not self._mappings_loaded:
            self.load_repository_mappings(repository)

        msg_id = str(message.get("message_id", "MSG_UNKNOWN"))
        msg_type = str(message.get("message_type", "text")).lower()
        raw_media_id = str(message.get("media_id", message.get("image_id", message.get("voice_note_id", "")))).strip()
        media_id = raw_media_id if raw_media_id and raw_media_id.lower() != "nan" else msg_id

        # 1. Non-media check
        if msg_type not in ["image", "voice", "audio", "video"] and not message.get("has_media") and raw_media_id.lower() in ["", "nan"]:
            return MediaResult(
                message_id=msg_id,
                media_type="none",
                processed=False,
                summary="Non-media text message.",
                classification="None",
                confidence=1.0,
            )

        # 2. Check Cache
        cached_res = self.cache.get(msg_id) or self.cache.get(media_id)
        if cached_res:
            return cached_res

        # 3. Process Image Media
        if msg_type == "image" or media_id in self.image_map or msg_id in self.image_map:
            path_str = self.image_map.get(media_id) or self.image_map.get(msg_id) or message.get("file_path")
            if path_str:
                resolved_file = Path(path_str)
            else:
                resolved_file = self._resolve_path(f"media/images/{media_id}.jpg", IMAGE_PATH)

            if not self._validate_media_file(resolved_file, VALID_IMAGE_EXTS):
                logger.warning(f"Missing, invalid, or corrupted image file for '{media_id}' at: {resolved_file}")
                res = MediaResult(
                    message_id=msg_id,
                    media_type="image",
                    processed=False,
                    summary="Missing, invalid, or corrupted image file.",
                    classification="Unknown",
                    confidence=0.0,
                )
                self.cache.set(msg_id, res)
                return res

            res = self.image_processor.process_image(resolved_file, message_id=msg_id)
            self.cache.set(msg_id, res)
            self.cache.set(media_id, res)
            return res

        # 4. Process Voice / Audio Media
        elif msg_type in ["voice", "audio"] or media_id in self.voice_map or msg_id in self.voice_map:
            path_str = self.voice_map.get(media_id) or self.voice_map.get(msg_id) or message.get("file_path")
            if path_str:
                resolved_file = Path(path_str)
            else:
                resolved_file = self._resolve_path(f"media/audio/{media_id}.mp3", VOICE_PATH)

            if not self._validate_media_file(resolved_file, VALID_AUDIO_EXTS):
                logger.warning(f"Missing, invalid, or corrupted voice file for '{media_id}' at: {resolved_file}")
                res = MediaResult(
                    message_id=msg_id,
                    media_type="voice",
                    processed=False,
                    summary="Missing, invalid, or corrupted audio file.",
                    classification="Unknown",
                    confidence=0.0,
                )
                self.cache.set(msg_id, res)
                return res

            res = self.voice_processor.process_voice(resolved_file, message_id=msg_id)
            self.cache.set(msg_id, res)
            self.cache.set(media_id, res)
            return res

        # Fallback
        res = MediaResult(
            message_id=msg_id,
            media_type="none",
            processed=False,
            summary="Unsupported or missing media format.",
            classification="Unknown",
            confidence=0.0,
        )
        self.cache.set(msg_id, res)
        return res

    def _resolve_path(self, file_path_str: str, default_dir: Path) -> Path:
        """Resolve raw file path string to absolute Path object.

        Args:
            file_path_str: Raw file path string from dataset.
            default_dir: Default fallback directory.

        Returns:
            Resolved Path object.
        """
        p = Path(file_path_str)
        if p.is_absolute() and p.exists():
            return p

        # Check relative to PROJECT_ROOT
        proj_p = PROJECT_ROOT / file_path_str
        if proj_p.exists():
            return proj_p

        # Check relative to DATASET_PATH
        data_p = DATASET_PATH / file_path_str
        if data_p.exists():
            return data_p

        # Check inside default_dir by filename
        dir_p = default_dir / p.name
        if dir_p.exists():
            return dir_p

        return (PROJECT_ROOT / file_path_str).resolve()

    def _validate_media_file(self, path: Path, valid_exts: set[str]) -> bool:
        """Validate media file existence, non-zero size, and extension.

        Args:
            path: Target file Path.
            valid_exts: Set of allowed extension strings.

        Returns:
            True if file is valid, else False.
        """
        if not path.exists() or not path.is_file():
            return False
        if path.stat().st_size == 0:
            return False
        if path.suffix.lower() not in valid_exts:
            return False
        return True
