# Quickstart: Phase 2 Image Processing and Quality Checking

## Prerequisites

- Phase 0 bootstrap is complete.
- Phase 1 OCR engine contracts are available for later integration, but Phase 2
  does not run OCR engines.
- Python 3.10 or newer.
- Local tests must run without internet, camera hardware, audio devices, OCR
  credentials, or paid services.

## Install Test Dependencies

```bash
python -m pip install -r requirements.txt
```

Phase 2 may add local image-processing dependencies such as OpenCV-compatible
image operations and `numpy`. Missing camera, audio, OCR, or online credentials
must not affect Phase 2 tests.

## Run Local Tests

```bash
python -m pytest tests/unit
```

Expected local coverage:

- Image input validation.
- Brightness status classification.
- Blur or sharpness status classification.
- Contrast status classification.
- Text-presence estimation without OCR.
- Overall quality report decisions.
- Conservative blocking for poor or uncertain images.
- Arabic and English guidance mapping.
- Preprocessing variants for accepted images.
- Rejected images do not automatically enter preprocessing.
- Default log metadata excludes image contents and OCR text.

## Optional Quality Commands

Run when installed:

```bash
python -m ruff check .
python -m black --check .
python -m mypy .
```

Optional tool absence is non-blocking when documented during implementation.

## Phase 2 Boundary

Phase 2 verifies local image quality and preprocessing only. It intentionally
excludes camera capture, depth analysis, best-frame selection, OCR engine
execution, OCR cascade routing, text cleanup, voice commands, TTS playback, and
translation.

## Validation Checklist

- Dark images are rejected with improve-lighting guidance.
- Bright or washed-out images are rejected or marked uncertain with corrective
  guidance.
- Blurry images are rejected with steadiness or recapture guidance.
- Low-contrast images are classified separately from acceptable images.
- No-text or unlikely-text images are blocked with point-to-text guidance.
- Borderline or uncertain images are blocked from the normal OCR path.
- Acceptable Arabic, English, and mixed-text fixtures pass quality assessment.
- Accepted images can produce `online_light`, `local_natural`, and
  `emergency_strong` variants.
- The original image is preserved during preprocessing.
- Default logs contain metadata only and no image contents or OCR text.

## Validation Results

Validated on 2026-05-17:

- `python -m pytest tests/unit`: passed, 71 tests.
- `python -m ruff check .`: passed.
- `python -m black --check .`: not installed in the active environment;
  non-blocking optional check.
- `python -m mypy .`: not installed in the active environment; non-blocking
  optional check.
- Phase 2 boundary scan for camera capture, depth analysis, best-frame
  selection, OCR execution, OCR cascade routing, text cleanup, voice commands,
  TTS, and translation in `modules/image_processing/`: passed.
- Default validation artifact check: `tests/fixtures/images/phase2/` contains
  only `README.md`; no generated debug image artifacts were created.
