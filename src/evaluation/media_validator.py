"""Media Pipeline Validation & Impact Analysis Tool for HackerRank Submission."""

import time
from pathlib import Path
import pandas as pd

from src.loaders.load_data import DataRepository
from src.builders.context_manager import ContextManager
from src.features.feature_pipeline import FeaturePipeline
from src.media.media_manager import MediaManager
from src.media.image.image_processor import ImageProcessor
from src.media.voice.voice_processor import VoiceProcessor
from src.utils.logger import logger


def run_media_validation():
    """Execute complete validation of image OCR and voice note speech pipelines."""
    project_root = Path(__file__).resolve().parent.parent.parent
    dataset_dir = project_root / "dataset"
    images_dir = dataset_dir / "media" / "images"
    audio_dir = dataset_dir / "media" / "audio"
    output_csv = project_root / "output" / "output.csv"

    repo = DataRepository(dataset_path=dataset_dir)
    repo.load_all()
    context = ContextManager(repo)
    context.build()

    fp = FeaturePipeline(context)
    mm = MediaManager(repository=repo)
    image_processor = ImageProcessor()
    voice_processor = VoiceProcessor()

    df_messages = repo.get_dataframe("messages")
    df_output = pd.read_csv(output_csv) if output_csv.exists() else pd.DataFrame()
    out_map = df_output.set_index("message_id").to_dict("index") if not df_output.empty else {}

    images_df = repo.get_dataframe("images")
    voice_df = repo.get_dataframe("voice_notes")

    img_map = dict(zip(images_df["image_id"], images_df["file_path"])) if "image_id" in images_df.columns else {}
    voice_map = dict(zip(voice_df["voice_note_id"], voice_df["file_path"])) if "voice_note_id" in voice_df.columns else {}

    # Reverse lookup from media_id / image_id / voice_note_id to message row
    msg_by_image = {}
    msg_by_voice = {}
    for _, row in df_messages.iterrows():
        m_id = str(row.get("message_id", ""))
        img_id = str(row.get("image_id", ""))
        v_id = str(row.get("voice_note_id", ""))
        if img_id and img_id != "nan":
            msg_by_image[img_id] = row.to_dict()
        if v_id and v_id != "nan":
            msg_by_voice[v_id] = row.to_dict()
        if m_id.startswith("msg_"):
            msg_by_image[m_id.replace("msg_", "img_")] = row.to_dict()
            msg_by_voice[m_id.replace("msg_", "vn_")] = row.to_dict()

    # --- Phase 2: OCR Image Processing ---
    image_files = sorted(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")))
    ocr_rows = []
    processed_images = 0
    failed_images = 0

    for img_path in image_files:
        filename = img_path.name
        img_id = img_path.stem
        start_time = time.perf_counter()
        
        try:
            m_res = image_processor.process_image(img_path, message_id=img_id)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            processed_images += 1
            
            # Extract text & word count
            ocr_text = m_res.summary
            word_count = len(ocr_text.split()) if ocr_text else 0
            
            # Lookup output routing decision
            msg_row = msg_by_image.get(img_id, {})
            msg_id = msg_row.get("message_id", f"msg_{img_id.replace('img_', '')}")
            out_info = out_map.get(msg_id, {})
            
            action = out_info.get("action", "unknown")
            msg_type = out_info.get("message_type", "unknown")
            reason = out_info.get("reason", "N/A")
            
            ocr_rows.append({
                "image_name": filename,
                "ocr_text": ocr_text,
                "ocr_confidence": m_res.confidence,
                "processing_time_ms": elapsed_ms,
                "word_count": word_count,
                "classification": m_res.classification,
                "message_id": msg_id,
                "action": action,
                "message_type": msg_type,
                "reason": reason
            })
        except Exception as e:
            failed_images += 1
            logger.error(f"Failed to process image {filename}: {e}")

    df_ocr = pd.DataFrame(ocr_rows)
    df_ocr.to_csv(project_root / "ocr_results.csv", index=False)

    # --- Phase 3: Speech Audio Processing ---
    audio_files = sorted(list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav")))
    speech_rows = []
    processed_audio = 0
    failed_audio = 0

    for audio_path in audio_files:
        filename = audio_path.name
        vn_id = audio_path.stem
        start_time = time.perf_counter()
        
        try:
            m_res = voice_processor.process_voice(audio_path, message_id=vn_id)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            processed_audio += 1
            
            transcript = m_res.summary
            word_count = len(transcript.split()) if transcript else 0
            
            msg_row = msg_by_voice.get(vn_id, {})
            msg_id = msg_row.get("message_id", f"msg_{vn_id.replace('vn_', '')}")
            out_info = out_map.get(msg_id, {})
            
            action = out_info.get("action", "unknown")
            msg_type = out_info.get("message_type", "unknown")
            reason = out_info.get("reason", "N/A")
            
            speech_rows.append({
                "audio_name": filename,
                "transcript": transcript,
                "speech_confidence": m_res.confidence,
                "processing_time_ms": elapsed_ms,
                "word_count": word_count,
                "classification": m_res.classification,
                "message_id": msg_id,
                "action": action,
                "message_type": msg_type,
                "reason": reason
            })
        except Exception as e:
            failed_audio += 1
            logger.error(f"Failed to process audio {filename}: {e}")

    df_speech = pd.DataFrame(speech_rows)
    df_speech.to_csv(project_root / "speech_results.csv", index=False)

    total_images = len(image_files)
    total_audio = len(audio_files)
    img_coverage = (processed_images / total_images * 100.0) if total_images > 0 else 0.0
    audio_coverage = (processed_audio / total_audio * 100.0) if total_audio > 0 else 0.0

    print(f"OCR Processing Complete: {processed_images}/{total_images} images ({img_coverage:.1f}% coverage)")
    print(f"Speech Processing Complete: {processed_audio}/{total_audio} voice notes ({audio_coverage:.1f}% coverage)")
    print(f"Saved ocr_results.csv ({len(df_ocr)} rows) and speech_results.csv ({len(df_speech)} rows)")


if __name__ == "__main__":
    run_media_validation()
