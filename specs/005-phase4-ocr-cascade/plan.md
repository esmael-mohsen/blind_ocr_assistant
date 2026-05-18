# Implementation Plan: Phase 4 OCR Cascade Controller

**Branch**: `005-phase4-ocr-cascade` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-phase4-ocr-cascade/spec.md`

## Summary

Implement the OCR cascade controller that turns the independent Phase 1 OCR
engines into one reliable OCR decision. Phase 4 will quality-score OCR output,
accept normal-mode online OCR only when it is good enough, fall back to local
accuracy OCR and then emergency OCR when needed, skip online OCR when offline or
disallowed, support High Accuracy Mode comparison, and return safe metadata for
later spoken feedback. The feature remains independent from camera capture,
best-frame selection, text cleanup, voice commands, TTS, translation, and full
assistant orchestration.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-3 modules; Phase 1 OCR engine
interfaces and `OCRResult`; Phase 2 image-quality readiness signals; Phase 3
selected-frame outputs as input only; dataclasses and enums for cascade models;
standard library timing for durations; optional `requests`-style online
availability checks; `pytest`, `pytest-mock`, and `pytest-cov` for deterministic
tests.

**Storage**: Local filesystem logs only. No database and no persistent OCR text
storage. Raw OCR text may pass through structured results for later cleanup but
is excluded from default logs. OCR text may be logged only when both debug mode
and explicit sensitive-text logging are enabled.

**Testing**: Unit tests for OCR quality scoring, threshold boundaries, normal
online cascade, weak-result fallback, offline routing, High Accuracy Mode
comparison, per-engine one-attempt limit, image-not-ready blocking, stable error
codes, deterministic tie-breaks, safe metadata/logging, and Phase 4 scope
boundaries. Integration-style tests use mocked OCR engines rather than live OCR
providers.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux for mocked OCR cascade tests.

**Project Type**: Single local Python assistant application with importable OCR
cascade modules.

**Performance Goals**: Normal mode attempts at most one engine at a time and
stops after the first acceptable result. Each allowed engine is attempted at
most once per cascade request by default. Online availability checks are short
and conservative. High Accuracy Mode may do extra comparison work only when
explicitly requested.

**Constraints**: No paid OCR service; no mandatory cloud dependency; no default
parallel execution of all OCR engines; no camera capture; no best-frame
selection; no text cleanup; no voice command recognition; no TTS playback; no
translation; no full assistant workflow. OCR quality acceptance threshold is
0.70. Image-not-ready inputs return `IMAGE_NOT_READY_FOR_OCR` without running
OCR.

**Scale/Scope**: One selected image per request, Arabic/English/mixed language
hints, one cascade decision result, and deterministic tests with mocked OCR
outcomes for online, local accuracy, and emergency OCR paths.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Cascade outcomes include OCR progress, fallback,
  success, and failure messages suitable for later spoken feedback, with no
  visual-only required workflow.
- Accuracy Before Speed: PASS. OCR output below 0.70 is weak and triggers
  fallback or failure rather than being silently accepted.
- Free Online-First, Offline-Fallback: PASS. Online OCR remains optional and
  replaceable; local accuracy and emergency OCR provide offline degraded mode.
- Graceful Degradation: PASS. Online unavailability, weak text, engine failure,
  and image-not-ready states return structured failures or next fallback paths.
- Privacy by Default: PASS. Only the selected image may be sent to online OCR
  when explicitly allowed; OCR text is not logged by default.
- Modular Engines: PASS. Cascade decisions use stable OCR engine interfaces and
  stay independent from camera, text cleanup, speaking, translation, and full
  assistant orchestration.
- Testability and Observability: PASS. Attempt path, selected engine, duration,
  quality score, fallback use, and failure reason are planned with mocked tests.
- Raspberry Pi Resource Awareness: PASS. Engines are attempted sequentially by
  default, with bounded retries and no default all-engine parallel execution.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 4 scoped to OCR quality and cascade routing with no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-phase4-ocr-cascade/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- ocr-cascade-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- ocr/
|   |-- __init__.py
|   |-- ocr_models.py
|   |-- base.py
|   |-- ocr_quality.py
|   `-- ocr_cascade.py
|-- image_processing/
|   `-- image_models.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_ocr_quality.py
|   |-- test_ocr_cascade.py
|   |-- test_ocr_cascade_logging_privacy.py
|   `-- test_ocr_cascade_scope_boundaries.py
`-- fixtures/
    `-- text/
        `-- ocr_quality_cases.md
```

**Structure Decision**: Extend the existing `modules/ocr/*` layer by adding
`ocr_quality.py` and `ocr_cascade.py`. Existing OCR engine wrappers remain
independent; camera, image processing, text cleanup, voice, translation, and
assistant modules are consumed only through stable data inputs or remain out of
scope.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 4.
