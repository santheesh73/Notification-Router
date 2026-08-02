# Multimodal Media Pipeline Architecture Map

**Target Modules**: `src/media/media_manager.py`, `src/media/image/`, `src/media/voice/`, `src/media/media_pipeline.py`  
**Status**: **`DISCOVERED & MAPPED`**

---

## 1. End-to-End Multimodal Data Flow Diagram

```text
                                INCOMING WHATSAPP MESSAGE
                                            │
                                            ▼
                           Phase 1: Media ID & Path Resolution
                   (media_id -> dataset/media/images/ or audio/)
                                            │
                                            ▼
                          Phase 2: Multimodal Validation & Preprocessing
                   (ImageValidator / TranscriptValidator)
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         IMAGE MEDIA PROCESSING                         VOICE NOTE MEDIA PROCESSING
       (ImageProcessor / ImageParser)                 (VoiceProcessor / TranscriptParser)
         OCR & Vision Abstraction                       Speech-to-Text Abstraction
         Extracted Text, Entities,                      Extracted Transcripts, Dates,
         Urgency & Risk Scores                          Times, Amounts, Speaker Count
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                             Phase 3: FeatureVector Enrichment
                            (has_media, media_type, text_content)
                                            │
                                            ▼
                            Phase 4: Deterministic Rule Engine
                           (Multimodal Emergency Hazards Override)
                                            │
                         ┌──────────────────┴──────────────────┐
                  Resolved (97.3%)                    Unresolved (2.7%)
                         │                                     │
                         │                         Phase 5: Historical Evidence
                         │                         Phase 6: Hybrid LLM Router
                         │                                     │
                         └──────────────────┬──────────────────┘
                                            │
                                            ▼
                             Phase 7: Decision Fusion Engine
                               (Final Action & Confidence)
                                            │
                                            ▼
                             Phase 8: Output CSV Prediction
                                      (output.csv)
```

---

## 2. Discovered Multimodal Components & Utilities

| Component Category | Implementation Module | Primary Responsibilities | Extracted Features / Data |
| :--- | :--- | :--- | :--- |
| **Media Repository Mapper** | `src/media/media_manager.py` | Maps `image_id` / `voice_note_id` to `dataset/media/` file paths | `image_map`, `voice_map`, cached file paths |
| **Image Preprocessor** | `src/media/image/image_validator.py` | Validates file existence, image headers, and extension bounds | `is_valid_image` boolean |
| **OCR & Vision Extractor** | `src/media/image/image_processor.py` | Vision AI model abstraction (OCR text extraction & scene classification) | `summary`, `classification`, `entities`, `confidence` |
| **Image Entity Parser** | `src/media/image/image_parser.py` | Normalizes vision AI extractions into structured `MediaResult` | `dates`, `times`, `amounts`, `people`, `organizations` |
| **Audio Preprocessor** | `src/media/voice/transcript_validator.py` | Validates audio header format, sample duration, and file size | `is_valid_audio` boolean |
| **Speech Transcribe Engine** | `src/media/voice/transcription.py` | Speech-to-Text audio transcription model abstraction (Whisper) | `text`, `language`, `duration_seconds`, `confidence` |
| **Voice Entity Parser** | `src/media/voice/transcript_parser.py` | Parses raw transcript text into structured domain entities | `summary`, `classification`, `entities`, `people` |
| **Multimodal Cache** | `src/media/media_cache.py` | Memory cache for OCR and Speech transcript outputs | SHA-256 keyed `MediaResult` cache |
| **Batch Pipeline Engine** | `src/media/media_pipeline.py` | Coordinates batch multimodal evaluation and metric summaries | Average OCR & Transcription confidence statistics |

---

## 3. Discovered Multimodal Routing Invocations

1. **Feature Vector Injection**: Media presence (`has_media = True`, `media_type = "image"` / `"voice"`) enriches `FeatureVector` text content with OCR / Speech transcripts.
2. **Multimodal Emergency Override**: In `ConflictResolver` (`src/confidence/conflict_resolver.py`), OCR/Speech emergency keywords (e.g. *"hospital"*, *"OTP"*, *"security alert"*) automatically trigger `notify` / `urgent` actions with `confidence = 0.95`.
3. **Unmuted Media Uncertainty Trigger**: In `ExecutionPipeline` (`src/pipeline/execution_pipeline.py`), unmuted media attachments without high-confidence rule matches ($\ge 0.85$) trigger AI LLM analysis.
