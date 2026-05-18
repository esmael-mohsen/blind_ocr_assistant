# Implementation Plan: Phase 5 Text Cleanup, RTL Handling, and Language Detection

**Branch**: `006-phase5-text-cleanup` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-phase5-text-cleanup/spec.md`

## Summary

Implement the text preparation layer that converts raw OCR output into clean,
readable text for later TTS and translation. Phase 5 will preserve raw OCR text,
produce a separate clean text value, normalize whitespace, line breaks, and
punctuation spacing, apply conservative OCR garbage cleanup, preserve Arabic and
mixed-language logical reading order, classify Arabic/English/mixed/unknown
text, and expose privacy-safe metadata and guidance. This phase does not run
OCR, capture camera frames, translate text, speak text aloud, parse voice
commands, or orchestrate the full assistant workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-4 modules; standard library
dataclasses, enums, and regular expressions; existing local logging/privacy
patterns; no external language detection, online service, paid API, or model
dependency for Phase 5.

**Storage**: Local filesystem logs only. No database and no persistent text
storage. Raw OCR text and clean text are returned in structured results but are
excluded from default logs. Text may appear in logs only when both debug mode
and explicit sensitive-text logging are enabled.

**Testing**: Unit tests for cleanup models, whitespace normalization, line-break
policy, punctuation spacing, conservative garbage cleanup, idempotence, Arabic
readability, English readability, mixed-language preservation, language evidence
thresholds, unknown/insufficient evidence, RTL logical order metadata, safe
metadata/logging, and Phase 5 scope boundaries.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux for pure text tests.

**Project Type**: Single local Python assistant application with importable text
cleanup and language detection modules.

**Performance Goals**: Process typical OCR text locally and synchronously with
small memory overhead. Cleanup should be deterministic, idempotent, and fast
enough to be negligible compared with OCR and later TTS. No network calls or
heavy model loading are allowed.

**Constraints**: No paid service; no mandatory cloud dependency; offline-only
logic; no OCR execution; no image processing; no camera capture; no translation;
no TTS playback; no voice command parsing; no assistant orchestration. Cleanup
must be conservative: preserve uncertain content with warnings instead of
deleting ambiguous text.

**Scale/Scope**: One raw OCR text payload per cleanup request, Arabic and
English as supported languages, mixed Arabic/English content, deterministic
fixture-driven tests, and result metadata safe for later workflow integration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Results include guidance text for empty, noisy, or
  uncertain text that later TTS can speak; no visual-only workflow is required.
- Accuracy Before Speed: PASS. Cleanup preserves uncertain content and reports
  warnings rather than aggressively deleting text that a blind user cannot
  visually verify.
- Free Online-First, Offline-Fallback: PASS. Phase 5 is fully local and
  offline-capable with no paid service, online API, or model dependency.
- Graceful Degradation: PASS. Empty, noisy, uncertain-language, and mixed
  direction cases return structured statuses, warnings, and user-safe guidance.
- Privacy by Default: PASS. Raw and clean text are excluded from default logs
  and require both debug mode and explicit sensitive-text logging to appear.
- Modular Engines: PASS. Text cleanup stays behind `modules.text` boundaries
  and does not couple to OCR engines, camera capture, translation, voice, or
  assistant orchestration.
- Testability and Observability: PASS. Planned tests cover Arabic, English,
  mixed, noisy, empty, idempotence, privacy, and scope boundaries with
  deterministic fixtures.
- Raspberry Pi Resource Awareness: PASS. The phase uses lightweight local text
  processing and avoids network calls, heavy models, and unbounded state.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 5 scoped to text cleanup, RTL handling, language detection, guidance, and
privacy-safe metadata with no constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-phase5-text-cleanup/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- text-cleanup-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- text/
|   |-- __init__.py
|   |-- cleanup.py
|   |-- language_detector.py
|   `-- rtl_fixer.py
|-- ocr/
|   `-- ocr_models.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_text_cleanup_models.py
|   |-- test_text_cleanup.py
|   |-- test_language_detector.py
|   |-- test_rtl_fixer.py
|   |-- test_text_logging_privacy.py
|   `-- test_text_scope_boundaries.py
`-- fixtures/
    `-- text/
        |-- cleanup_cases.md
        `-- language_detection_cases.md
```

**Structure Decision**: Use the existing `modules/text/*` package reserved by
the project structure. Keep cleanup, language detection, and RTL utilities
separate so later TTS and translation phases can consume stable structured
results without coupling to OCR engine internals.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 5.
