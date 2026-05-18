# Quickstart: Phase 5 Text Cleanup, RTL Handling, and Language Detection

## Prerequisites

- Python 3.10+
- Existing Phase 0-4 project setup
- Raw OCR text produced by Phase 4 or deterministic fixture text
- `pytest`

Automated validation uses text fixtures only. It does not require camera
hardware, live OCR credentials, internet access, TTS, translation, or audio
devices.

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

## Run Automated Phase 5 Tests

```powershell
python -m pytest tests/unit/test_text_cleanup_models.py
python -m pytest tests/unit/test_text_cleanup.py
python -m pytest tests/unit/test_language_detector.py
python -m pytest tests/unit/test_rtl_fixer.py
python -m pytest tests/unit/test_text_logging_privacy.py
python -m pytest tests/unit/test_text_scope_boundaries.py
python -m pytest tests/unit
```

Expected automated coverage:

- Raw OCR text is preserved exactly.
- Clean text is produced separately.
- Repeated spaces, tabs, line breaks, and punctuation spacing are normalized.
- Single OCR line breaks inside paragraphs are collapsed.
- Blank-line paragraph breaks and list-like breaks remain readable.
- Conservative cleanup preserves uncertain fragments and returns warnings.
- Cleanup is idempotent.
- Arabic text remains readable.
- English text remains readable.
- Mixed Arabic/English text preserves both language segments.
- Dominant language detection uses the 60% evidence rule.
- Insufficient evidence returns unknown rather than a false dominant language.
- RTL and mixed text preserve logical reading order with direction metadata.
- Default logs exclude raw text and clean text.
- Phase 5 does not call OCR, camera, translation, voice, TTS, or assistant
  workflow modules.

## Manual Acceptance Checklist

- Arabic fixture text remains understandable after cleanup.
- English fixture text remains understandable after cleanup.
- Mixed Arabic/English fixture text is not destroyed.
- No meaningful text is deleted solely because it is uncertain.
- Empty text returns user-safe guidance rather than an exception.
- Safe metadata helps troubleshoot status, language, direction, and warnings
  without exposing private text.

## Local-Only Behavior

Phase 5 is fully local. It must not use online services, paid APIs, cloud
storage, camera hardware, OCR engines, translation engines, voice recognition,
or TTS playback.

## Validation Results

Record validation after implementation:

```text
python -m pytest tests/unit -> 164 passed
python -m ruff check . -> All checks passed
python -m black --check . -> not installed in this environment
python -m mypy . -> not installed in this environment
```
