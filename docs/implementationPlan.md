# Blind OCR Assistant — Implementation Plan

> **Purpose of this file:**  
> This document is the detailed technical implementation plan for Spec Kit `/speckit.plan`, task generation, and phased development execution.
>
> **Primary Goal:** Build a free, online-first, offline-fallback OCR + translation + voice assistant system for blind users on Raspberry Pi 4 using Orbbec Astra Pro.
>
> **Important:** This plan intentionally avoids paid OCR, paid translation, paid STT, and paid TTS services.

---

## 1. Implementation Plan Metadata

```text
Feature: Assistive OCR Reading System
Suggested Branch: 001-assistive-ocr-reading
Target Device: Raspberry Pi 4 Model B, 4GB RAM
Camera: Orbbec Astra Pro
Primary Languages: Arabic, English
Architecture Style: Modular Python service with engine cascade
Execution Model: Voice command → guided capture → best frame → OCR cascade → cleanup → read/translate
Cost Policy: Free-only APIs and local open-source fallbacks
```

---

## 2. Technical Context

### 2.1 Language and Runtime

```text
Language: Python
Version: Python 3.10 or newer
Target OS: Linux on Raspberry Pi
Runtime Style: Long-running local assistant process
```

---

### 2.2 Primary Dependencies

Core:

```text
opencv-python or opencv-python-headless
numpy
requests or httpx
python-dotenv
pydantic or dataclasses
```

OCR:

```text
OCR.space Free API
PaddleOCR
Tesseract OCR
pytesseract or subprocess wrapper
```

Camera:

```text
Orbbec SDK / OpenNI2 / compatible camera access layer
OpenCV VideoCapture fallback where applicable
```

Voice:

```text
Vosk
sounddevice or pyaudio
eSpeak NG
Optional later: Piper TTS
```

Translation:

```text
LibreTranslate HTTP client
Argos Translate
```

Testing:

```text
pytest
pytest-mock
pytest-cov
```

Optional tooling:

```text
ruff
black
mypy
pre-commit
```

---

### 2.3 Storage

No database is required for the initial version.

Use local filesystem storage only:

```text
logs/
debug_captures/
benchmark_results/
config/
```

Storage policy:

- Logs are local.
- Debug image saving is optional and disabled by default.
- Raw text and clean text may be logged only when debug mode is enabled.
- No cloud storage is used.

---

### 2.4 Target Platform

```text
Primary: Raspberry Pi 4 Model B, 4GB RAM
Development: Linux laptop or Windows with WSL for non-camera modules
Deployment: Raspberry Pi OS / Ubuntu-based Raspberry Pi environment
```

---

### 2.5 Performance Goals

Accuracy is the highest priority, but the implementation should still target:

```text
Normal online OCR workflow:
- Complete reading workflow ideally within 5–15 seconds depending on image and network.

Offline PaddleOCR workflow:
- Accept slower response if accuracy improves.

Memory:
- Avoid sustained memory pressure above safe Raspberry Pi limits.
- Lazy-load heavy models where possible.

Capture:
- Select best frame from 10–20 frames.
```

---

### 2.6 Hard Constraints

```text
No paid services.
No mandatory cloud dependency.
No OCR on every video frame.
No full parallel OCR execution by default.
Must support Arabic and English.
Must support offline degraded mode.
Must provide voice guidance for blind users.
Must preserve modular engine architecture.
```

---

## 3. Constitution Check

Before implementation, the following gates must pass.

### 3.1 Accessibility Gate

- [ ] Every user-facing state has a voice response.
- [ ] No required workflow depends on visual UI.
- [ ] Capture errors are explained verbally.
- [ ] OCR failure is explained verbally.
- [ ] Translation failure is explained verbally.

---

### 3.2 Cost Gate

- [ ] No paid OCR APIs are required.
- [ ] No paid translation APIs are required.
- [ ] No paid STT/TTS APIs are required.
- [ ] All external services have local fallback or free mode.

---

### 3.3 Offline Fallback Gate

- [ ] OCR.space failure triggers PaddleOCR.
- [ ] PaddleOCR failure triggers Tesseract.
- [ ] LibreTranslate failure triggers Argos Translate.
- [ ] Online STT failure allows Vosk command grammar.
- [ ] The system can still read text without internet, with reduced quality if needed.

---

### 3.4 Raspberry Pi Resource Gate

- [ ] Heavy engines are lazy-loaded.
- [ ] OCR engines are not run in parallel by default.
- [ ] Frame capture count is bounded.
- [ ] Debug image storage is bounded.
- [ ] Model loading does not crash 4GB RAM target.
- [ ] Long-running process releases camera and audio resources correctly.

---

### 3.5 Privacy Gate

- [ ] Images are not stored permanently unless debug mode is enabled.
- [ ] OCR text is not logged in production mode unless configured.
- [ ] No user data is sent to paid services.
- [ ] Online OCR uploads only the selected best frame, not continuous video.

---

### 3.6 Testability Gate

- [ ] OCR engines have interface-level tests.
- [ ] OCR cascade has unit tests.
- [ ] Quality checker has deterministic tests.
- [ ] Text cleanup has Arabic/English test cases.
- [ ] Command parser has Arabic/English tests.
- [ ] Benchmark script exists before final tuning.

---

## 4. Project Structure

Recommended repository structure:

```text
blind_ocr_assistant/
│
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── modules/
│   │
│   ├── camera/
│   │   ├── __init__.py
│   │   ├── orbbec_camera.py
│   │   ├── frame_selector.py
│   │   ├── depth_analyzer.py
│   │   └── camera_models.py
│   │
│   ├── image_processing/
│   │   ├── __init__.py
│   │   ├── preprocessing.py
│   │   ├── quality_checker.py
│   │   ├── text_region_detector.py
│   │   └── image_models.py
│   │
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── ocr_space_client.py
│   │   ├── paddle_ocr_engine.py
│   │   ├── tesseract_engine.py
│   │   ├── ocr_quality.py
│   │   ├── ocr_cascade.py
│   │   └── ocr_models.py
│   │
│   ├── text/
│   │   ├── __init__.py
│   │   ├── cleanup.py
│   │   ├── language_detector.py
│   │   ├── rtl_fixer.py
│   │   └── segmentation.py
│   │
│   ├── translation/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── libre_translate_client.py
│   │   ├── argos_fallback.py
│   │   └── translation_models.py
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── stt_online.py
│   │   ├── vosk_fallback.py
│   │   ├── command_parser.py
│   │   ├── tts_engine.py
│   │   └── voice_models.py
│   │
│   ├── assistant/
│   │   ├── __init__.py
│   │   ├── dialogue_manager.py
│   │   ├── reading_controller.py
│   │   ├── translation_controller.py
│   │   └── state.py
│   │
│   └── common/
│       ├── __init__.py
│       ├── logging.py
│       ├── errors.py
│       ├── result.py
│       └── constants.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   │   ├── images/
│   │   └── text/
│   └── benchmark/
│
├── scripts/
│   ├── run_assistant.sh
│   ├── benchmark_ocr.py
│   ├── test_camera.py
│   ├── test_tts.py
│   └── install_pi_dependencies.sh
│
├── docs/
│   ├── architecture.md
│   ├── commands.md
│   ├── troubleshooting.md
│   └── benchmark_methodology.md
│
└── specs/
    └── 001-assistive-ocr-reading/
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        ├── contracts/
        └── tasks.md
```

---

## 5. Core Data Models

### 5.1 FrameCandidate

```text
FrameCandidate
- id
- rgb_image
- depth_map optional
- timestamp
- sharpness_score
- brightness_score
- contrast_score
- text_area_score
- stability_score
- distance_score
- total_score
```

---

### 5.2 ImageQualityReport

```text
ImageQualityReport
- is_acceptable
- brightness_status
- blur_status
- distance_status
- angle_status
- text_presence_status
- spoken_guidance_message
- quality_score
```

---

### 5.3 OCRRequest

```text
OCRRequest
- image
- language_hints: ["ar", "en"]
- mode: normal | high_accuracy
- preprocessing_variant
- allow_online
- allow_offline
```

---

### 5.4 OCRResult

```text
OCRResult
- engine_name
- raw_text
- clean_text optional
- confidence optional
- quality_score
- duration_ms
- success
- error_message optional
- fallback_used
```

---

### 5.5 TranslationRequest

```text
TranslationRequest
- source_text
- source_language
- target_language
- allow_online
- allow_offline
```

---

### 5.6 TranslationResult

```text
TranslationResult
- engine_name
- translated_text
- source_language
- target_language
- duration_ms
- success
- error_message optional
```

---

### 5.7 AssistantState

```text
AssistantState
- current_mode
- last_raw_text
- last_clean_text
- last_translated_text
- last_ocr_engine
- is_reading
- is_paused
- internet_available
```

---

## 6. Engine Strategy

### 6.1 OCR Cascade

Default order:

```text
1. OCR.space Free API
2. PaddleOCR
3. Tesseract ara+eng
```

Decision rules:

```text
If internet is available:
    Run OCR.space first.
    If result is good:
        accept result.
    Else:
        run PaddleOCR.
        If PaddleOCR is good:
            accept result.
        Else:
            run Tesseract.

If internet is unavailable:
    Run PaddleOCR first.
    If result is good:
        accept result.
    Else:
        run Tesseract.
```

High Accuracy Mode:

```text
If user requests high accuracy:
    Run OCR.space if online.
    Run PaddleOCR.
    Compare quality scores.
    Accept the better result.
    Run Tesseract only if both fail.
```

---

### 6.2 OCR Quality Scoring

The first implementation should use simple deterministic scoring:

```text
score = base_score
      + length_score
      + language_ratio_score
      + line_consistency_score
      - weird_symbol_penalty
      - excessive_spacing_penalty
      - repeated_character_penalty
```

Quality thresholds:

```text
GOOD_RESULT_THRESHOLD = configurable
WEAK_RESULT_THRESHOLD = configurable
```

Initial weak-result indicators:

- Empty text.
- Very short text.
- Too many non-letter symbols.
- Excessive broken spacing.
- Arabic text with severe fragmentation.
- Output inconsistent with visible text-area score.

---

### 6.3 Preprocessing Variants

For OCR.space:

```text
variant_online_light:
- resize if needed
- light contrast enhancement
- optional sharpening
```

For PaddleOCR:

```text
variant_paddle_natural:
- original or lightly enhanced
- optional deskew
- optional crop
```

For Tesseract:

```text
variant_tesseract_strong:
- grayscale
- denoise
- adaptive threshold
- deskew
- sharpen
```

---

## 7. Voice Assistant Strategy

### 7.1 STT Strategy

Primary:

```text
Online STT through Web Speech / browser SpeechRecognition when available.
```

Fallback:

```text
Vosk Arabic + English command grammar.
```

Vosk should not be used as open dictation in the initial version.  
It should recognize a controlled set of commands only.

---

### 7.2 Command Parser

Command categories:

```text
READ_TEXT
READ_HIGH_ACCURACY
TRANSLATE_TO_ARABIC
TRANSLATE_TO_ENGLISH
REPEAT
STOP
CONTINUE
TRY_AGAIN
READ_SLOWLY
READ_FASTER
REPEAT_LAST_SENTENCE
REPEAT_LAST_PARAGRAPH
```

The parser must support Arabic and English variants.

---

### 7.3 TTS Strategy

Initial:

```text
eSpeak NG
```

Later improvement:

```text
Piper TTS
```

The TTS engine must support:

- Speak.
- Stop.
- Pause if available.
- Continue if available.
- Repeat last sentence.
- Repeat last paragraph.
- Adjustable rate.

---

## 8. Implementation Phases

---

# Phase 0 — Repository Bootstrap and Environment Setup

## Objective

Prepare the repository, virtual environment, basic project structure, and Raspberry Pi dependency assumptions.

## Tasks

1. Create repository structure.
2. Add `requirements.txt`.
3. Add `.env.example`.
4. Add `config.py`.
5. Add central logging utility.
6. Add common `Result` pattern for success/failure responses.
7. Add README with project purpose and hardware requirements.
8. Add scripts directory.
9. Add initial test folders.
10. Add development quality tools if practical.

## Deliverables

```text
Repository skeleton
Configuration file
Logging module
README
Install script draft
```

## Acceptance Criteria

- Project imports successfully.
- `python main.py --help` or equivalent entrypoint works.
- Unit test runner works.
- No OCR/camera functionality is required yet.

---

# Phase 1 — OCR Engine Prototype

## Objective

Implement and test the three OCR engines independently before building the cascade.

## Tasks

### OCR.space

1. Create `OCRBaseEngine` interface.
2. Implement `OCRSpaceClient`.
3. Read API key from `.env`.
4. Send image file or image bytes to OCR.space.
5. Parse response.
6. Return `OCRResult`.
7. Handle network errors and API errors.

### PaddleOCR

1. Implement `PaddleOCREngine`.
2. Lazy-load PaddleOCR model.
3. Support Arabic and English configuration.
4. Return `OCRResult`.
5. Capture duration and errors.

### Tesseract

1. Install Tesseract and Arabic/English data.
2. Implement `TesseractEngine`.
3. Use `ara+eng`.
4. Support PSM configuration.
5. Return `OCRResult`.

## Deliverables

```text
modules/ocr/base.py
modules/ocr/ocr_space_client.py
modules/ocr/paddle_ocr_engine.py
modules/ocr/tesseract_engine.py
basic OCR engine tests
```

## Acceptance Criteria

- Each OCR engine can process a local test image independently.
- Each engine returns consistent `OCRResult`.
- Engine failure does not crash the program.
- PaddleOCR is lazy-loaded, not loaded at import time.

---

# Phase 2 — Image Processing and Quality Checking

## Objective

Prevent low-quality images from reaching OCR whenever possible.

## Tasks

1. Implement brightness scoring.
2. Implement blur/sharpness scoring using Laplacian variance or equivalent.
3. Implement contrast scoring.
4. Implement basic text-region estimation.
5. Implement preprocessing variants.
6. Implement `ImageQualityReport`.
7. Implement voice guidance message mapping.

## Deliverables

```text
modules/image_processing/quality_checker.py
modules/image_processing/preprocessing.py
modules/image_processing/text_region_detector.py
unit tests for quality checks
```

## Acceptance Criteria

- Dark images are detected.
- Blurry images are detected.
- Acceptable images pass quality check.
- The system returns actionable guidance messages.
- Preprocessing returns separate variants for OCR.space, PaddleOCR, and Tesseract.

---

# Phase 3 — Camera Integration and Best Frame Selection

## Objective

Connect the Orbbec Astra Pro and select the best frame for OCR.

## Tasks

1. Implement camera abstraction.
2. Implement Orbbec RGB capture.
3. Implement depth capture if available.
4. Implement depth-based distance estimation.
5. Implement frame capture burst.
6. Implement frame scoring.
7. Select best frame from 10–20 frames.
8. Add camera test script.

## Deliverables

```text
modules/camera/orbbec_camera.py
modules/camera/depth_analyzer.py
modules/camera/frame_selector.py
scripts/test_camera.py
```

## Acceptance Criteria

- Camera can capture RGB frame.
- Depth analysis returns meaningful distance status when available.
- Best-frame selector chooses a stable/sharp frame.
- Camera resources are released after capture.
- If depth is unavailable, system still works with RGB-only mode.

---

# Phase 4 — OCR Cascade Controller

## Objective

Build the intelligent OCR cascade that chooses when to accept or fallback.

## Tasks

1. Implement `OCRQualityChecker`.
2. Implement `OCRCascade`.
3. Add online availability check.
4. Implement default cascade:
   - OCR.space
   - PaddleOCR
   - Tesseract
5. Implement offline cascade:
   - PaddleOCR
   - Tesseract
6. Implement High Accuracy Mode:
   - OCR.space + PaddleOCR comparison.
7. Add structured logging of selected engine and fallback path.

## Deliverables

```text
modules/ocr/ocr_quality.py
modules/ocr/ocr_cascade.py
integration tests for fallback behavior
```

## Acceptance Criteria

- Good OCR.space result is accepted.
- Weak OCR.space result triggers PaddleOCR.
- PaddleOCR failure triggers Tesseract.
- Offline mode skips OCR.space.
- High Accuracy Mode compares OCR.space and PaddleOCR.
- Logs show engine path clearly.

---

# Phase 5 — Text Cleanup, RTL Handling, and Language Detection

## Objective

Prepare Arabic and English OCR output for reading and translation.

## Tasks

1. Implement basic OCR garbage cleanup.
2. Fix excessive spaces.
3. Fix line breaks.
4. Normalize punctuation spacing.
5. Add Arabic RTL handling utilities.
6. Add language detection for Arabic, English, and mixed text.
7. Preserve `raw_text` and `clean_text`.

## Deliverables

```text
modules/text/cleanup.py
modules/text/rtl_fixer.py
modules/text/language_detector.py
tests for Arabic/English/mixed text
```

## Acceptance Criteria

- Arabic text remains readable.
- English text remains readable.
- Mixed text is not destroyed by cleanup.
- Raw OCR output is preserved.
- Clean text is suitable for TTS.

---

# Phase 6 — TTS Reading Controller

## Objective

Read full text aloud and provide playback control.

## Tasks

1. Implement `TTSEngine` abstraction.
2. Implement eSpeak NG engine.
3. Add speak/stop controls.
4. Add speech rate configuration.
5. Segment text into sentences and paragraphs.
6. Implement repeat last sentence.
7. Implement repeat last paragraph.
8. Implement reading controller state.

## Deliverables

```text
modules/voice/tts_engine.py
modules/text/segmentation.py
modules/assistant/reading_controller.py
scripts/test_tts.py
```

## Acceptance Criteria

- System can read Arabic text.
- System can read English text.
- System can stop reading.
- System can repeat last sentence.
- System can repeat last paragraph.
- Reading state is tracked.

---

# Phase 7 — Translation Layer

## Objective

Translate the latest OCR text between Arabic and English using free online and offline options.

## Tasks

1. Implement `TranslationEngine` interface.
2. Implement LibreTranslate client.
3. Implement Argos Translate fallback.
4. Implement source language detection integration.
5. Implement target language command handling.
6. Add translation result reading through TTS.
7. Add error handling for unavailable services.

## Deliverables

```text
modules/translation/base.py
modules/translation/libre_translate_client.py
modules/translation/argos_fallback.py
modules/assistant/translation_controller.py
translation tests
```

## Acceptance Criteria

- Arabic text can be translated to English.
- English text can be translated to Arabic.
- LibreTranslate failure triggers Argos.
- Translation result is read aloud.
- The system uses the latest clean OCR text.

---

# Phase 8 — Voice Assistant Command System

## Objective

Allow Arabic and English voice control for the full reading workflow.

## Tasks

1. Implement command model.
2. Implement command parser.
3. Add Arabic command variants.
4. Add English command variants.
5. Implement Vosk fallback command recognizer.
6. Add online STT integration placeholder or browser/web integration boundary.
7. Route commands to reading and translation controllers.
8. Add spoken confirmations.

## Deliverables

```text
modules/voice/command_parser.py
modules/voice/vosk_fallback.py
modules/voice/stt_online.py
modules/assistant/dialogue_manager.py
command parser tests
```

## Acceptance Criteria

- Arabic read command is recognized.
- English read command is recognized.
- Translation commands are recognized.
- Repeat/stop/continue commands are recognized.
- Unknown commands produce helpful voice feedback.
- Vosk fallback works for fixed commands.

---

# Phase 9 — Full Assistive Workflow Integration

## Objective

Connect all modules into the complete user workflow.

## Tasks

1. Implement main assistant loop.
2. Connect voice commands to capture workflow.
3. Connect capture to OCR cascade.
4. Connect OCR result to text cleanup.
5. Connect text cleanup to TTS reading.
6. Connect translation commands to latest clean text.
7. Add user-facing spoken status messages.
8. Add robust exception handling.
9. Add graceful shutdown.

## Deliverables

```text
main.py
modules/assistant/dialogue_manager.py
modules/assistant/state.py
end-to-end workflow tests where possible
```

## Acceptance Criteria

The following scenario works:

```text
User: "اقرأ النص"
System: gives capture guidance.
System: selects best frame.
System: performs OCR cascade.
System: reads full text.
User: "ترجم للإنجليزي"
System: translates latest text.
System: reads translated text.
```

---

# Phase 10 — Benchmarking and Accuracy Tuning

## Objective

Measure real-world OCR performance and improve the pipeline.

## Tasks

1. Create benchmark image dataset.
2. Include Arabic, English, and mixed text.
3. Include real-world scenarios:
   - book page
   - printed document
   - medicine package
   - receipt
   - sign
   - low light
   - angled image
   - far image
   - blurry image
4. Add expected text files for selected samples.
5. Run OCR.space, PaddleOCR, and Tesseract separately.
6. Record duration, text length, quality score, and errors.
7. Tune preprocessing thresholds.
8. Tune OCR quality thresholds.
9. Tune frame selector scoring.

## Deliverables

```text
tests/benchmark/
scripts/benchmark_ocr.py
benchmark_results/
docs/benchmark_methodology.md
```

## Acceptance Criteria

- Benchmark can be run with one command.
- Results identify best engine per scenario.
- Quality checker thresholds are adjusted based on data.
- Known failure cases are documented.

---

# Phase 11 — Raspberry Pi Deployment Hardening

## Objective

Make the system reliable on real Raspberry Pi hardware.

## Tasks

1. Test memory usage.
2. Test camera stability.
3. Test PaddleOCR model loading.
4. Test offline mode.
5. Test no-internet startup.
6. Test audio input/output.
7. Add service startup option.
8. Add dependency install script.
9. Add troubleshooting documentation.
10. Add safe log rotation.

## Deliverables

```text
scripts/install_pi_dependencies.sh
scripts/run_assistant.sh
docs/troubleshooting.md
optional systemd service file
```

## Acceptance Criteria

- System starts on Raspberry Pi.
- Camera test passes.
- TTS test passes.
- OCR.space path works online.
- PaddleOCR path works offline.
- Tesseract path works as emergency fallback.
- System recovers from temporary internet failure.
- System can be stopped safely.

---

## 9. Testing Strategy

### 9.1 Unit Tests

Must cover:

```text
OCR quality scoring
Image quality scoring
Command parsing
Text cleanup
Language detection
Translation fallback selection
OCR cascade routing
```

---

### 9.2 Integration Tests

Must cover:

```text
OCR.space client with mocked API
PaddleOCR wrapper with sample image
Tesseract wrapper with sample image
Cascade fallback behavior
Translation fallback behavior
TTS controller behavior
```

---

### 9.3 Manual Hardware Tests

Must cover:

```text
Orbbec camera capture
Depth guidance
Audio input
Audio output
Voice command recognition
End-to-end read workflow
End-to-end translate workflow
Offline workflow
```

---

### 9.4 Acceptance Test Scenarios

Scenario 1:

```text
Arabic printed document → OCR → full Arabic reading
```

Scenario 2:

```text
English printed document → OCR → full English reading
```

Scenario 3:

```text
Mixed Arabic/English text → OCR → readable output
```

Scenario 4:

```text
Internet off → PaddleOCR fallback → reading
```

Scenario 5:

```text
PaddleOCR failure simulated → Tesseract fallback → reading
```

Scenario 6:

```text
User asks translation Arabic → English
```

Scenario 7:

```text
User asks translation English → Arabic
```

Scenario 8:

```text
Poor image → system gives capture guidance instead of OCR immediately
```

---

## 10. Configuration Plan

Use `.env` for secrets and environment-specific values:

```text
OCR_SPACE_API_KEY=
LIBRETRANSLATE_URL=
DEBUG_SAVE_IMAGES=false
LOG_LEVEL=INFO
HIGH_ACCURACY_MODE=false
FRAME_CAPTURE_COUNT=15
TESSERACT_LANGS=ara+eng
```

Use `config.py` for typed defaults:

```python
LANGUAGES = ["ar", "en"]

ONLINE_FIRST = True
OFFLINE_FALLBACK = True

OCR_PRIMARY = "ocr_space"
OCR_FALLBACK_1 = "paddleocr"
OCR_FALLBACK_2 = "tesseract"

TRANSLATION_PRIMARY = "libretranslate"
TRANSLATION_FALLBACK = "argos"

STT_PRIMARY = "web_speech"
STT_FALLBACK = "vosk"

TTS_PRIMARY = "espeak"
TTS_BETTER_OPTION = "piper"

FRAME_CAPTURE_COUNT = 15
READ_FULL_TEXT = True
```

---

## 11. Error Handling Policy

All engines must return structured failures, not throw uncaught exceptions.

Examples:

```text
OCR_SPACE_NETWORK_ERROR
OCR_SPACE_API_ERROR
PADDLEOCR_MODEL_LOAD_ERROR
TESSERACT_NOT_INSTALLED
NO_TEXT_DETECTED
IMAGE_TOO_BLURRY
IMAGE_TOO_DARK
TRANSLATION_SERVICE_UNAVAILABLE
VOSK_MODEL_NOT_FOUND
TTS_ENGINE_ERROR
```

Each error must map to a spoken message.

Example:

```text
OCR_SPACE_NETWORK_ERROR
→ "الاتصال غير متاح، سأستخدم القراءة المحلية."

IMAGE_TOO_BLURRY
→ "الصورة غير واضحة، ثبّت الكاميرا وحاول مرة أخرى."

NO_TEXT_DETECTED
→ "لم أجد نصًا واضحًا، حرّك الكاميرا ببطء."
```

---

## 12. Logging and Debugging Policy

Log levels:

```text
INFO:
- workflow start/end
- selected OCR engine
- fallback path

WARNING:
- weak OCR result
- poor image quality
- fallback used

ERROR:
- engine failure
- camera failure
- translation failure

DEBUG:
- raw OCR text
- clean OCR text
- image paths
- scoring details
```

Production default:

```text
DEBUG_SAVE_IMAGES=false
LOG_LEVEL=INFO
```

Debug mode:

```text
DEBUG_SAVE_IMAGES=true
LOG_LEVEL=DEBUG
```

---

## 13. Definition of Done

The feature is done when:

- [ ] The user can say "اقرأ النص" and trigger the workflow.
- [ ] The system gives spoken capture guidance.
- [ ] The system captures and selects the best frame.
- [ ] OCR.space works as online primary.
- [ ] PaddleOCR works as fallback.
- [ ] Tesseract works as emergency fallback.
- [ ] OCR result quality determines fallback.
- [ ] Arabic text cleanup works.
- [ ] English text cleanup works.
- [ ] Mixed text remains readable.
- [ ] The system reads full text aloud.
- [ ] The user can request Arabic ↔ English translation.
- [ ] Translation is read aloud.
- [ ] Offline degraded mode works.
- [ ] Logs show engine decisions.
- [ ] Benchmark script exists.
- [ ] Raspberry Pi deployment instructions exist.
- [ ] No paid service is required.

---

## 14. Suggested Spec Kit Task Generation Prompt

Use this after the constitution and spec are created:

```text
/speckit.plan

Create a detailed implementation plan for the Blind OCR Assistant using the architecture and phases in implementationPlan.md. The system must run on Raspberry Pi 4 with Orbbec Astra Pro, use OCR.space Free API as online primary OCR, PaddleOCR as offline accuracy fallback, Tesseract ara+eng as emergency fallback, LibreTranslate as free translation primary, Argos Translate as offline translation fallback, online STT primary with Vosk fallback, and eSpeak NG initial TTS. The plan must enforce accessibility-first design, free-only services, offline graceful degradation, modular engine interfaces, image-quality guidance before OCR, best-frame selection, Arabic/English cleanup, RTL handling, benchmarking, and Raspberry Pi resource limits.
```

Then generate tasks:

```text
/speckit.tasks
```

Then implement:

```text
/speckit.implement
```

---

## 15. Final Implementation Summary

Build the system in this order:

```text
1. Repository skeleton
2. OCR engines individually
3. Image quality and preprocessing
4. Camera capture and best-frame selection
5. OCR cascade
6. Text cleanup and RTL handling
7. TTS reading
8. Translation
9. Voice command assistant
10. Full workflow integration
11. Benchmarking and tuning
12. Raspberry Pi deployment hardening
```

The core technical rule:

```text
Do not OCR bad images.
Do not run all engines by default.
Do guide the user before capture.
Do use cascade fallback.
Do preserve free-only architecture.
Do prioritize accessibility and accuracy.
