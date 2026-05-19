# Implementation Plan: Phase 7 Translation Layer

**Branch**: `008-phase7-translation-layer` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-phase7-translation-layer/spec.md`

## Summary

Implement the translation layer that consumes Phase 5 clean text, translates
between Arabic and English, and hands successful translated results to the Phase
6 reading layer when available. Phase 7 adds a stable translation engine
boundary, a free online translation client, a local offline fallback, translated
result validation, online-first/offline-fallback routing, same-language no-op
handling, mixed or unknown source-language guidance, latest-only translation
state, reading handoff, and privacy-safe metadata. This phase does not capture
camera frames, run OCR, clean text, parse voice commands, or orchestrate the
full assistant workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-6 modules; standard library
dataclasses, enums, timing, and optional import boundaries; existing text
language detection utilities; existing Phase 6 reading controller boundary;
`requests` or compatible HTTP client already identified by the project plan for
the free online translation client; optional local Argos Translate dependency
loaded lazily for offline fallback. No paid translation service or mandatory
cloud dependency is required.

**Storage**: Local filesystem logs only. No database and no persistent
translation history. Normal in-memory translation state keeps only the latest
source clean-text identity and latest translated result, replacing them on each
new request. Default logs exclude raw OCR text, clean text, translated text, and
snippets.

**Testing**: Unit tests for translation models, safe metadata, online client
response handling, lazy local fallback loading, cascade routing, translated
result validation, same-language no-op behavior, mixed or unknown language
guidance, all-provider failure, reading handoff, latest-only state replacement,
privacy-safe logging, and Phase 7 scope boundaries. Live online translation is
optional and must be skipped unless explicitly configured.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux through mocked online and
offline translation tests.

**Project Type**: Single local Python assistant application with importable
translation engines and a translation controller.

**Performance Goals**: Keep translation routing sequential and bounded. Online
translation should return quickly when available; offline fallback may be slower
but must avoid import-time model loading. Translation operations should record
duration and selected path for safe observability.

**Constraints**: No paid service; no mandatory cloud dependency; online
translation is optional and replaceable; offline fallback is local and
lazy-loaded; no OCR execution; no camera capture; no image processing; no text
cleanup; no voice command parsing; no full assistant orchestration. Mixed or
unknown source text requires an explicit supported source language before
translation. Invalid translated results trigger fallback when available.

**Scale/Scope**: One latest clean-text payload and one latest translated result
in memory at a time. Supported directions are Arabic-to-English and
English-to-Arabic for Phase 7.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Translation start, success, fallback, no-text,
  same-language, unsupported-language, mixed or unknown language, reading
  handoff, and failure outcomes all return user-safe spoken guidance.
- Accuracy Before Speed: PASS. Phase 7 validates translated results and avoids
  unsafe mixed or unknown language guesses unless an explicit supported source
  language is supplied.
- Free Online-First, Offline-Fallback: PASS. Online translation is free,
  optional, replaceable, and backed by a local offline fallback.
- Graceful Degradation: PASS. Disabled, unavailable, timed-out, failing, or
  invalid online translation falls back locally when allowed; final failure is
  structured and human-understandable.
- Privacy by Default: PASS. Raw OCR text, clean text, translated text, and
  snippets are excluded from default logs and debug artifacts.
- Modular Engines: PASS. Translation engines stay behind `modules.translation`
  interfaces and translation orchestration stays in `modules.assistant`, with a
  narrow optional reading-layer handoff.
- Testability and Observability: PASS. Planned tests use deterministic mocked
  engines while recording safe metadata such as selected path, duration,
  fallback use, validity status, and failure category.
- Raspberry Pi Resource Awareness: PASS. Offline translation is lazy-loaded,
  routing is sequential, no provider runs in parallel by default, and state is
  latest-only.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 7 scoped to translation, fallback routing, result validation, latest-only
state, reading handoff, and privacy-safe metadata with no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/008-phase7-translation-layer/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- translation-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- translation/
|   |-- __init__.py
|   |-- base.py
|   |-- libre_translate_client.py
|   |-- argos_fallback.py
|   `-- translation_models.py
|-- assistant/
|   |-- __init__.py
|   `-- translation_controller.py
|-- text/
|   |-- language_detector.py
|   `-- cleanup.py
|-- voice/
|   `-- tts_engine.py
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_translation_models.py
|   |-- test_translation_base.py
|   |-- test_libre_translate_client.py
|   |-- test_argos_fallback.py
|   |-- test_translation_controller.py
|   |-- test_translation_logging_privacy.py
|   `-- test_translation_scope_boundaries.py
`-- fixtures/
    `-- text/
        `-- translation_cases.md
```

**Structure Decision**: Use the existing `modules/translation` package reserved
by the project structure for provider models and engines, and add
`modules/assistant/translation_controller.py` for routing and reading handoff.
Keep provider-specific code separate from controller logic so online and
offline translation options can be replaced without changing assistant
workflow code.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 7.
