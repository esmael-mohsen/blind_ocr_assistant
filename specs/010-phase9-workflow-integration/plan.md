# Implementation Plan: Phase 9 Full Assistive Workflow Integration

**Branch**: `010-phase9-workflow-integration` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-phase9-workflow-integration/spec.md`

## Summary

Integrate the existing Phase 0-8 modules into one complete assistive assistant
session. Phase 9 adds the main workflow coordinator, assistant state, read
workflow orchestration from command to capture to OCR to cleanup to TTS,
translation orchestration using the latest clean text, spoken status handoffs,
single-active-read protection, recoverable timeout/failure handling,
privacy-safe workflow metadata, and graceful operational shutdown. This phase
does not add new OCR engines, translation engines, speech engines, cleanup
rules, command categories, benchmark tooling, deployment hardening, visual UI,
user accounts, or cloud storage.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-8 modules; standard library
dataclasses, enums, signal handling, timing, and typing protocols; existing
camera capture and best-frame selection; existing image quality reports;
existing OCR cascade; existing text cleanup and language detection; existing
reading controller; existing translation controller; existing command parser
and dialogue manager. No new paid or mandatory cloud dependency is required.

**Storage**: Local filesystem logs only. No database and no persistent workflow
history. Normal session state keeps latest successful raw text, clean text,
translation, detected language, selected OCR engine, fallback flags, current
workflow status, and last user-safe guidance. Default logs exclude images, raw
OCR text, clean text, translated text, command transcripts, snippets, provider
secrets, and debug artifacts.

**Testing**: Unit tests for assistant state, workflow result models, read
workflow orchestration, translation workflow handoff, busy read rejection,
recapture guidance after all frames are rejected, timeout recovery, shutdown
cleanup, privacy-safe logging, and Phase 9 scope boundaries. Integration tests
use mocked or controlled module boundaries for complete read and translate
flows. Manual hardware checks cover Orbbec or RGB capture, audio output, Arabic
read-to-translate, English read-to-translate, and offline degraded mode where
hardware and local engines are available.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B, with development support on Windows/Linux through mocked camera,
OCR, translation, command, and speech boundaries.

**Project Type**: Single local Python assistive application with importable
assistant workflow services and a CLI/runtime entrypoint.

**Performance Goals**: Complete normal online read workflow within the
project target of roughly 5-15 seconds when camera, network, and OCR services
are healthy. Keep capture bounded to configured frame count. Run OCR through
the existing cascade, not all engines in parallel by default. Keep workflow
status updates immediate and component timeouts recoverable.

**Constraints**: No paid service; no mandatory cloud dependency; no visual UI
requirement; no continuous every-frame OCR; no full parallel OCR execution by
default; one active read workflow at a time; no automatic repeated capture loop
after all frames are rejected; voice stop remains playback control; shutdown is
operational through process interruption, service stop, or test harness; heavy
engines remain lazy-loaded behind existing boundaries; all user-facing states
return spoken guidance.

**Scale/Scope**: One local assistant session, one active read workflow, one
latest successful clean-text payload, and one latest translated result in
memory at a time. Supported content languages remain Arabic, English, and
mixed text. Supported command-driven workflows are read, translate to Arabic,
translate to English, playback controls, help/status guidance through existing
command behavior, and operational shutdown.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. The plan requires spoken guidance for command
  recognition, capture start/progress, capture rejection, OCR progress,
  fallback use, cleanup outcome, reading start, translation start/completion,
  recoverable failures, busy read rejection, and shutdown.
- Accuracy Before Speed: PASS. The read workflow uses existing quality checks,
  best-frame selection, preprocessing/OCR cascade, cleanup, and recapture
  guidance before reading text aloud.
- Free Online-First, Offline-Fallback: PASS. Phase 9 only orchestrates
  existing free/optional online and offline fallback boundaries and adds no
  paid dependency.
- Graceful Degradation: PASS. Camera, quality, OCR, cleanup, translation, TTS,
  command, timeout, and unexpected failures become structured results with
  spoken recovery guidance and safe state preservation.
- Privacy by Default: PASS. Default workflow logs contain only safe metadata
  such as status, selected engine, fallback category, duration, and error code;
  sensitive content and image payloads are excluded.
- Modular Engines: PASS. Orchestration depends on existing controllers and
  callable boundaries, not provider internals.
- Testability and Observability: PASS. The plan defines deterministic mocked
  end-to-end tests, scope-boundary tests, safe logging tests, and manual
  hardware acceptance checks.
- Raspberry Pi Resource Awareness: PASS. The plan keeps one active workflow,
  bounded capture, sequential cascade routing, lazy engine loading, explicit
  cleanup, and recoverable timeouts.

Post-design re-check: PASS. Research, data model, contract, and quickstart keep
Phase 9 scoped to integration and state orchestration with no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/010-phase9-workflow-integration/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- workflow-integration-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
main.py
config.py

modules/
|-- assistant/
|   |-- __init__.py
|   |-- dialogue_manager.py
|   |-- reading_controller.py
|   |-- state.py
|   |-- translation_controller.py
|   `-- workflow.py
|-- camera/
|   |-- camera_models.py
|   |-- frame_selector.py
|   `-- orbbec_camera.py
|-- image_processing/
|   |-- image_models.py
|   |-- preprocessing.py
|   `-- quality_checker.py
|-- ocr/
|   |-- ocr_cascade.py
|   `-- ocr_models.py
|-- text/
|   |-- cleanup.py
|   `-- language_detector.py
|-- translation/
|   |-- base.py
|   |-- translation_models.py
|   `-- ...
|-- voice/
|   |-- command_models.py
|   |-- command_parser.py
|   |-- tts_engine.py
|   `-- ...
`-- common/
    |-- logging.py
    `-- result.py

tests/
|-- unit/
|   |-- test_assistant_state.py
|   |-- test_assistant_workflow.py
|   |-- test_assistant_workflow_failures.py
|   |-- test_assistant_workflow_logging_privacy.py
|   |-- test_assistant_workflow_scope_boundaries.py
|   `-- test_main_assistant_entrypoint.py
`-- integration/
    |-- test_full_read_workflow.py
    `-- test_full_translate_workflow.py
```

**Structure Decision**: Keep Phase 9 orchestration in `modules.assistant`
because it coordinates previously built assistant, camera, OCR, text,
translation, and voice boundaries. Add `modules/assistant/state.py` for
session state and `modules/assistant/workflow.py` for the read/translate
workflow coordinator. Keep `main.py` thin as a runtime entrypoint that wires
configured dependencies and delegates to the coordinator.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 9.
