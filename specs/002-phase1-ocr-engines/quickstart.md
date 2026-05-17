# Quickstart: Phase 1 OCR Engine Prototype

## Prerequisites

- Phase 0 bootstrap is complete.
- Python 3.10 or newer.
- Local tests must run without internet, camera hardware, audio devices, or paid
  OCR credentials.

Optional for live/manual checks:

- Free online OCR credential.
- Local accuracy OCR package/model.
- Emergency OCR executable with Arabic and English language data.

## Install Test Dependencies

```bash
python -m pip install -r requirements.txt
```

Phase 1 may add optional OCR dependencies. Missing optional OCR engines must
produce structured failures or skipped live tests, not unrelated local test
failures.

## Run Local Tests

```bash
python -m pytest tests/unit
```

Expected local coverage:

- OCR request/result validation.
- Common OCR interface behavior.
- Missing credential failure.
- Mocked online provider success, timeout, malformed response, and one retry.
- Local accuracy lazy loading.
- Emergency engine missing executable/language-data failures.
- Empty or weak OCR output classification.
- Default log metadata excludes raw OCR text.

## Optional Live Online Test

Set a free online OCR credential, then opt in to the live test path documented by
the implementation tasks.

Expected behavior without credentials:

- Live online OCR test is skipped.
- Local unit tests still pass.

## Phase 1 Boundary

Phase 1 verifies independent OCR engines only. It intentionally excludes camera
capture, image-quality pre-checking, best-frame selection, OCR cascade routing,
text cleanup, voice commands, TTS reading, and translation.

## Validation Checklist

- Each engine can be invoked independently through the shared OCR interface.
- Available engines return engine name, raw text, duration, and success status
  for readable fixtures.
- Expected failures return stable error codes and human-readable messages.
- Importing the project or running bootstrap help does not load the heavy local
  accuracy model.
- Default logs contain metadata only and no raw OCR text.

## Validation Results

Validated on 2026-05-17:

- `python -m pytest tests/unit`: passed, 43 tests.
- `python -m pytest tests/integration/test_ocr_live_optional.py`: skipped
  without `OCR_SPACE_API_KEY`.
- `python -m ruff check .`: passed.
- `python -m black --check .`: not installed in the active environment;
  non-blocking optional check.
- `python -m mypy .`: not installed in the active environment; non-blocking
  optional check.
- Phase 1 boundary scan for camera capture, image quality, frame selection, OCR
  cascade routing, text cleanup, voice commands, TTS, and translation in OCR
  implementation paths: passed.
