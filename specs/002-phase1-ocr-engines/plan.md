# Implementation Plan: Phase 1 OCR Engine Prototype

**Branch**: `002-phase1-ocr-engines` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-phase1-ocr-engines/spec.md`

## Summary

Implement and validate three OCR engines independently behind a shared OCR
interface: a free online primary engine, a local accuracy fallback, and an
emergency OCR fallback. Each engine must return a consistent structured result,
handle expected failure modes without crashing, record safe metadata, avoid
default raw-text logging, and remain independently testable before the later OCR
cascade phase.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0 bootstrap modules; `requests` or
`httpx` for the free online OCR client; PaddleOCR as optional local accuracy
engine; Tesseract via `pytesseract` or subprocess as emergency engine; `pytest`,
`pytest-mock`, and `pytest-cov` for tests.

**Storage**: Local filesystem only. Small test fixtures may live under
`tests/fixtures/images/`; debug image saving remains disabled by default. No
database and no cloud storage.

**Testing**: Unit tests for OCR request/result models, interface contract,
failure classification, lazy loading, logging privacy, timeout/retry behavior,
and mocked engine responses. Optional live online test is opt-in and skipped
without free credentials.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Linux and Windows/WSL for non-hardware
engine tests.

**Project Type**: Single local Python assistant application with importable OCR
engine modules.

**Performance Goals**: Engine calls record duration. Online requests use a
configurable timeout and at most one retry for transient failures. Heavy local
engine model loading occurs only when OCR is requested, not during import or
bootstrap help.

**Constraints**: No paid OCR service, no mandatory cloud dependency, no camera
capture, no image-quality pre-checking, no best-frame selection, no OCR cascade,
no text cleanup, no voice commands, no TTS, and no translation in Phase 1.

**Scale/Scope**: Three independently invokable OCR engines and their shared data
contracts; one image per request; small local fixtures and mockable inputs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Engines return stable error codes and
  human-readable messages that can later be mapped to spoken feedback.
- Accuracy Before Speed: PASS. Empty or weak output is classified as
  `NO_TEXT_DETECTED` or `WEAK_OCR_RESULT` instead of successful OCR, and result
  metadata supports later quality evaluation.
- Free Online-First, Offline-Fallback: PASS. Online OCR is free-only and
  optional; local accuracy and emergency engines are validated independently.
- Graceful Degradation: PASS. Missing credentials, provider errors, model load
  failures, executable/language-data failures, and no-text outcomes return
  structured failures without uncaught exceptions.
- Privacy by Default: PASS. Default logs include metadata only and exclude raw
  OCR text unless debug text logging is explicitly enabled later.
- Modular Engines: PASS. All engines implement the common OCR interface and
  remain independent of future cascade orchestration.
- Testability and Observability: PASS. Plan includes interface tests, mocked
  provider responses, fixture-driven local tests, duration capture, and stable
  failure codes.
- Raspberry Pi Resource Awareness: PASS. Heavy local OCR is lazy-loaded and no
  OCR engines run in parallel by default.

Post-design re-check: PASS. Research, data model, contracts, and quickstart keep
Phase 1 scoped to independent OCR engines and introduce no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-phase1-ocr-engines/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- ocr-engine-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- ocr/
|   |-- __init__.py
|   |-- base.py
|   |-- ocr_models.py
|   |-- ocr_space_client.py
|   |-- paddle_ocr_engine.py
|   `-- tesseract_engine.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_ocr_models.py
|   |-- test_ocr_base.py
|   |-- test_ocr_space_client.py
|   |-- test_paddle_ocr_engine.py
|   |-- test_tesseract_engine.py
|   `-- test_ocr_logging_privacy.py
|-- integration/
|   `-- test_ocr_live_optional.py
`-- fixtures/
    |-- images/
    |   |-- arabic_sample.txt
    |   |-- english_sample.txt
    |   `-- mixed_sample.txt
    `-- text/
        `-- ocr_expected_notes.md
```

**Structure Decision**: Extend the Phase 0 modular scaffold by implementing only
the OCR engine layer. Phase 1 owns `modules/ocr/*` and OCR-specific tests. The
future cascade controller, image processing, camera, voice, TTS, translation,
and text cleanup modules remain out of scope.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 1.
