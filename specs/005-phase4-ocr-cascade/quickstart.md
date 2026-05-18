# Quickstart: Phase 4 OCR Cascade Controller

## Prerequisites

- Python 3.10+
- Existing Phase 0-3 project setup
- Independent OCR engine wrappers from Phase 1
- Image readiness signals from Phase 2 or equivalent request field
- `pytest`

Automated validation uses mocked OCR engines and does not require live OCR
credentials, camera hardware, or internet access.

## Install Development Dependencies

```powershell
python -m pip install -r requirements.txt
```

Optional quality tools:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy .
```

## Run Automated Phase 4 Tests

```powershell
python -m pytest tests/unit/test_ocr_quality.py tests/unit/test_ocr_cascade.py
python -m pytest tests/unit/test_ocr_cascade_logging_privacy.py
python -m pytest tests/unit/test_ocr_cascade_scope_boundaries.py
python -m pytest tests/unit
```

Expected automated coverage:

- OCR quality score accepts `0.70+` and rejects scores below `0.70`
- empty, very short, symbol-heavy, repeated-character, excessive-spacing, Arabic,
  English, and mixed-language cases are classified deterministically
- normal online mode accepts good online OCR without fallback
- weak online OCR falls back to local accuracy OCR
- weak local accuracy OCR falls back to emergency OCR
- offline mode skips online OCR and uses local accuracy first
- image-not-ready inputs return `IMAGE_NOT_READY_FOR_OCR` without engine calls
- each engine is attempted at most once by default
- High Accuracy Mode compares online and local accuracy results
- High Accuracy Mode similar-score tie-break prefers local accuracy within 0.05
- default logs exclude OCR text and image contents
- Phase 4 does not call camera, text cleanup, voice, TTS, translation, or
  assistant workflow modules

The automated tests use mocked OCR engines. Offline and online-unavailable
scenarios must not call the online engine or upload image bytes; they should
route to local accuracy OCR first and emergency OCR second.

## Manual Acceptance Checklist

- Normal mode accepts the first good OCR result.
- Weak OCR results trigger fallback before failure.
- Offline mode remains usable without online OCR.
- High Accuracy Mode compares stronger candidates and preserves deterministic
  tie-breaking.
- Final failures include guidance suitable for later spoken feedback.
- Default logs show selected engine and fallback path without private OCR text.

## Validation Results

Record validation after implementation:

```text
python -m pytest tests/unit -> 129 passed
python -m ruff check . -> All checks passed
python -m black --check . -> not installed in this environment
python -m mypy . -> not installed in this environment
```
