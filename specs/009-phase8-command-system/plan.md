# Implementation Plan: Phase 8 Voice Assistant Command System

**Branch**: `009-phase8-command-system` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-phase8-command-system/spec.md`

## Summary

Implement a fixed-command voice assistant layer that recognizes curated Arabic
and English commands for read, stop, continue, repeat sentence, repeat
paragraph, translate to Arabic, translate to English, and help. Phase 8 adds a
stable command model, deterministic command parser, optional online STT
boundary, lazy local fixed-command fallback, dialogue manager routing to the
existing reading and translation boundaries, spoken guidance, latest-only safe
command state, and privacy-safe metadata. This phase does not capture camera
frames, run OCR, process images, clean OCR text, perform translation itself,
synthesize new TTS behavior, or orchestrate the complete end-to-end assistant
workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-7 modules; standard library
dataclasses, enums, regex/text normalization, timing, and optional import
boundaries; existing Phase 6 reading controller boundary; existing Phase 7
translation controller boundary; optional local Vosk dependency loaded lazily
for offline fixed-command recognition. Online STT remains optional and
replaceable through a no-op boundary until a live provider is configured.

**Storage**: Local filesystem logs only. No database and no persistent command
history. Normal in-memory dialogue state keeps only the latest safe command
metadata, selected recognition path, fallback use, routed action status, and
guidance. Raw speech, recognized phrase text, OCR text, clean text, and
translated text are discarded after classification and excluded from default
logs.

**Testing**: Unit tests for command models, safe metadata, deterministic Arabic
and English command parsing, ambiguity handling, unknown/no-command guidance,
online STT boundary behavior, lazy Vosk fallback loading, online-first/local
fallback routing, dialogue manager routing to reading and translation
controllers, help command behavior, latest-only state, privacy-safe logging,
and Phase 8 scope boundaries. Live microphone and live online STT checks are
optional and skipped unless explicitly configured.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux through mocked recognizer and
controller tests.

**Project Type**: Single local Python assistant application with importable
voice command recognizers and an assistant dialogue manager.

**Performance Goals**: Keep command matching bounded and deterministic. Fixed
command parsing should be immediate for short phrases. Recognition routing must
be sequential, bounded by timeouts, and observable through safe metadata.

**Constraints**: No paid service; no mandatory cloud dependency; online STT is
optional and replaceable; Vosk fallback is local and lazy-loaded; command scope
is fixed and curated; no open-ended conversation; no camera capture; no OCR; no
image processing; no text cleanup; no translation execution; no new TTS engine;
no full workflow orchestration. Route actions only when exactly one supported
intent is confidently recognized.

**Scale/Scope**: One latest command attempt and latest safe dialogue state in
memory at a time. Supported languages are Arabic and English. Supported intents
are read, stop, continue, repeat sentence, repeat paragraph, translate to
Arabic, translate to English, and help.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Recognized, unknown, ambiguous, empty, failed,
  fallback, help, and unavailable-state commands return spoken guidance and do
  not require visual confirmation.
- Accuracy Before Speed: PASS. Command routing requires exactly one confidently
  recognized supported intent and avoids unsafe guessing for low-confidence or
  multi-intent phrases.
- Free Online-First, Offline-Fallback: PASS. Online STT is optional,
  replaceable, and backed by local fixed-command fallback.
- Graceful Degradation: PASS. Disabled, unavailable, timed-out, failing, or
  unsupported online recognition falls back locally when allowed; final failure
  is structured and user-safe.
- Privacy by Default: PASS. Raw speech, recognized phrase text, OCR text, clean
  text, translated text, and snippets are discarded or excluded from default
  logs and safe metadata.
- Modular Engines: PASS. STT/recognizer code stays behind `modules.voice`
  boundaries and command routing stays in `modules.assistant`, with narrow
  reading and translation handoffs.
- Testability and Observability: PASS. Planned tests use deterministic mocked
  recognizers and controllers while recording safe metadata such as selected
  path, fallback use, result status, command intent, and failure category.
- Raspberry Pi Resource Awareness: PASS. Local Vosk resources are lazy-loaded,
  recognition routing is sequential, command catalog matching is bounded, and
  state is latest-only.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 8 scoped to fixed command recognition, fallback routing, command routing,
spoken guidance, latest-only safe state, and privacy-safe metadata with no
constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/009-phase8-command-system/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- command-system-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- voice/
|   |-- command_models.py
|   |-- command_parser.py
|   |-- vosk_fallback.py
|   `-- stt_online.py
|-- assistant/
|   |-- dialogue_manager.py
|   |-- reading_controller.py
|   `-- translation_controller.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_command_models.py
|   |-- test_command_parser.py
|   |-- test_vosk_fallback.py
|   |-- test_stt_online.py
|   |-- test_dialogue_manager.py
|   |-- test_command_logging_privacy.py
|   `-- test_command_scope_boundaries.py
`-- fixtures/
    `-- voice/
        `-- command_phrases.md
```

**Structure Decision**: Use `modules.voice` for command models, deterministic
parser, online STT boundary, and local Vosk fallback. Use
`modules.assistant.dialogue_manager` for command routing to existing reading
and translation boundaries. Keep recognizer-specific code separate from routing
so online and local recognition can be replaced without changing assistant
workflow logic.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 8.
