# Implementation Plan: Phase 2 Image Processing and Quality Checking

**Branch**: `003-phase2-image-quality` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-phase2-image-quality/spec.md`

## Summary

Implement the local image-processing layer that decides whether a still image is
ready for OCR, returns bilingual recapture guidance when quality is poor or
uncertain, estimates likely text presence, and produces named preprocessing
variants for the later online, local accuracy, and emergency OCR paths. The
feature remains independent from camera capture, OCR execution, best-frame
selection, voice playback, text cleanup, and translation.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0/1 modules; OpenCV-compatible image
operations through `opencv-python-headless` or `opencv-python`; `numpy` for image
arrays and deterministic fixture generation; dataclasses or enums for structured
models; `pytest`, `pytest-mock`, and `pytest-cov` for tests.

**Storage**: Local filesystem only. Deterministic generated images or safe local
fixtures may live under `tests/fixtures/images/phase2/`. Debug image saving stays
disabled by default. No database and no cloud storage.

**Testing**: Unit tests for image model validation, brightness classification,
blur/sharpness classification, contrast classification, text-presence estimation,
overall quality decisions, bilingual guidance mapping, preprocessing variants,
privacy-safe metadata, and structured failures. Tests assert named categories and
decisions rather than exact threshold numbers.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Linux and Windows/WSL for non-camera image
processing tests.

**Project Type**: Single local Python assistant application with importable
image-processing modules.

**Performance Goals**: Evaluate one still image at a time. Quality assessment
and preprocessing should complete quickly enough to preserve the future 5-15
second reading workflow budget. Processing must avoid unbounded loops, repeated
full-image copies beyond named variants, and continuous frame analysis in Phase
2.

**Constraints**: No paid services, no online service, no camera hardware, no OCR
credential, no OCR engine execution, no cascade routing, no depth analysis, no
best-frame selection, no voice command recognition, no TTS playback, no text
cleanup, and no translation in Phase 2. Borderline or uncertain images are
blocked from the normal OCR path with recapture guidance.

**Scale/Scope**: One image input per request; quality report plus optional
preprocessing variants; deterministic generated or safe local fixtures covering
dark, bright, blurry, low contrast, no text, acceptable, Arabic, English, and
mixed text cases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Quality reports include short Arabic and English
  guidance messages suitable for later spoken feedback, and no essential
  workflow depends on visual inspection.
- Accuracy Before Speed: PASS. Poor and uncertain images are blocked before OCR,
  preventing unreliable reading output.
- Free Online-First, Offline-Fallback: PASS. Phase 2 uses local image analysis
  only and requires no paid, online, OCR, camera, audio, STT, TTS, or translation
  service.
- Graceful Degradation: PASS. Missing, unreadable, unsupported, poor, and
  uncertain images return structured statuses and corrective guidance instead of
  uncaught exceptions.
- Privacy by Default: PASS. Default logs contain metadata only; image contents
  and extracted text are not logged or stored. Debug image saving remains
  explicitly disabled by default.
- Modular Engines: PASS. Image quality and preprocessing stay independent from
  OCR engines, cascade routing, camera capture, command handling, TTS, and
  translation.
- Testability and Observability: PASS. Deterministic fixtures, category-based
  assertions, safe metadata, quality scores, statuses, and failure reasons are
  planned.
- Raspberry Pi Resource Awareness: PASS. The feature processes one still image
  at a time and avoids continuous frame analysis, unbounded artifact creation, or
  heavy model loading.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 2 scoped to local image quality and preprocessing, with no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-phase2-image-quality/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- image-processing-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- image_processing/
|   |-- __init__.py
|   |-- image_models.py
|   |-- quality_checker.py
|   |-- preprocessing.py
|   `-- text_region_detector.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_image_models.py
|   |-- test_quality_checker.py
|   |-- test_preprocessing.py
|   |-- test_text_region_detector.py
|   `-- test_image_logging_privacy.py
`-- fixtures/
    `-- images/
        `-- phase2/
            |-- README.md
            |-- acceptable_english.png
            |-- acceptable_arabic.png
            |-- acceptable_mixed.png
            |-- dark.png
            |-- blurry.png
            |-- low_contrast.png
            |-- no_text.png
            `-- borderline.png
```

**Structure Decision**: Extend the existing modular scaffold by adding only the
`modules/image_processing/*` layer and Phase 2-specific tests/fixtures. OCR,
camera, assistant, voice, text cleanup, and translation modules remain out of
scope except for consuming existing common logging/result utilities.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 2.
