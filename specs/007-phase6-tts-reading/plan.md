# Implementation Plan: Phase 6 TTS Reading Controller

**Branch**: `007-phase6-tts-reading` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-phase6-tts-reading/spec.md`

## Summary

Implement the local text-to-speech reading layer that consumes Phase 5 clean
text and reads it aloud in Arabic or English. Phase 6 will add a stable TTS
engine boundary, an initial eSpeak NG adapter, sentence and paragraph
segmentation, playback controls, speech-rate clamping, repeat-last-sentence and
repeat-last-paragraph behavior, and privacy-safe reading state. This phase does
not capture camera frames, run OCR, clean text, translate text, parse voice
commands, or orchestrate the full assistant workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-5 modules; standard library
dataclasses, enums, regular expressions, subprocess boundary for eSpeak NG, and
existing local logging/privacy patterns. No paid TTS service, cloud speech
provider, or heavy neural TTS dependency is required for Phase 6.

**Storage**: Local filesystem logs only. No database and no persistent spoken
text storage. Reading state may keep the current clean text and repeatable
segments in memory for the active process, but default logs must exclude raw
text, clean text, spoken text, and segment snippets.

**Testing**: Unit tests for TTS models, mocked speech engine behavior, eSpeak NG
adapter command construction with subprocess mocked, Arabic and English
segmentation, mixed text logical order, reading controller state transitions,
pause fallback, continue fallback, stop idempotence, rate default and clamping,
repeat behavior, structured TTS failures, privacy-safe logging, and Phase 6
scope boundaries.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux through mocked TTS engine
tests. Live eSpeak NG smoke testing is optional and hardware/environment
dependent.

**Project Type**: Single local Python assistant application with importable TTS,
text segmentation, and reading controller modules.

**Performance Goals**: Start reading without heavy model loading, keep
controller operations synchronous and lightweight, and avoid network calls.
Speech requests should be bounded to one selected engine invocation per
operation, with mocked tests covering behavior deterministically.

**Constraints**: No paid service; no mandatory cloud dependency; local free TTS
as the initial path; no OCR execution; no camera capture; no image processing;
no text cleanup; no translation; no voice command parsing; no full assistant
orchestration. Speech rate defaults to 150 words per minute and accepted rates
are clamped to 80-220 words per minute. Pause/resume must degrade gracefully
when the engine does not support native pause/resume.

**Scale/Scope**: One active reading session and one current clean-text payload
at a time, with deterministic sentence and paragraph segment lists used for
reading controls and repeat operations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Every read, stop, pause, continue, rate, repeat,
  empty-text, and TTS-failure operation returns user-safe spoken guidance and
  does not depend on visual confirmation.
- Accuracy Before Speed: PASS. Phase 6 reads the Phase 5 clean text in logical
  order and avoids guessing progress; repeat behavior uses the last
  successfully requested segment or the current segment when progress is
  unknown.
- Free Online-First, Offline-Fallback: PASS. The initial TTS path uses free
  local eSpeak NG behavior behind a replaceable engine interface with no paid or
  billing-required dependency.
- Graceful Degradation: PASS. Missing or failing TTS engines, unsupported
  pause/resume, empty text, and unavailable repeat history return structured
  failures and guidance instead of crashing or speaking unrelated text.
- Privacy by Default: PASS. Raw OCR text, clean text, spoken text, and segment
  snippets are excluded from default logs and debug artifacts.
- Modular Engines: PASS. TTS engine behavior stays behind `modules.voice`
  interfaces and reading orchestration stays in `modules.assistant`, separate
  from OCR, camera, cleanup, translation, and command parsing.
- Testability and Observability: PASS. Planned tests use deterministic fixtures
  and mocked engines while recording safe metadata such as engine name, outcome,
  duration, operation, fallback use, and failure category.
- Raspberry Pi Resource Awareness: PASS. Phase 6 avoids heavy model loading,
  cloud calls, unbounded queues, and parallel engine execution; eSpeak NG is
  invoked through a bounded local adapter.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 6 scoped to local TTS reading, playback control, segmentation, repeat
history, state transitions, structured errors, and privacy-safe metadata with no
constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/007-phase6-tts-reading/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- tts-reading-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- voice/
|   |-- __init__.py
|   |-- tts_engine.py
|   `-- voice_models.py
|-- text/
|   |-- __init__.py
|   `-- segmentation.py
|-- assistant/
|   |-- __init__.py
|   `-- reading_controller.py
`-- common/
    |-- logging.py
    |-- errors.py
    `-- result.py

tests/
|-- unit/
|   |-- test_tts_models.py
|   |-- test_tts_engine.py
|   |-- test_text_segmentation.py
|   |-- test_reading_controller.py
|   |-- test_tts_logging_privacy.py
|   |-- test_tts_scope_boundaries.py
|   `-- test_tts_script.py
`-- fixtures/
    `-- text/
        `-- segmentation_cases.md

scripts/
`-- test_tts.py
```

**Structure Decision**: Use the existing `modules/voice`, `modules/text`, and
`modules/assistant` packages reserved by the project structure. Keep the speech
engine adapter, reusable voice data models, deterministic segmentation, and
reading-state controller separate so later command routing and translation
phases can consume the controller without coupling to eSpeak NG internals.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 6.
