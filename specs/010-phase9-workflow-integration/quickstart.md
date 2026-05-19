# Phase 9 Quickstart: Full Assistive Workflow Integration

## Purpose

Phase 9 connects the existing command, camera, frame selection, image quality,
OCR cascade, text cleanup, reading, and translation modules into one complete
assistant workflow. It focuses on orchestration, latest safe state, spoken
status, recoverable failures, privacy-safe logging, and graceful shutdown.

## Expected Files

```text
main.py
modules/assistant/state.py
modules/assistant/workflow.py
modules/assistant/dialogue_manager.py
modules/assistant/reading_controller.py
modules/assistant/translation_controller.py
tests/unit/test_assistant_state.py
tests/unit/test_assistant_workflow.py
tests/unit/test_assistant_workflow_failures.py
tests/unit/test_assistant_workflow_logging_privacy.py
tests/unit/test_assistant_workflow_scope_boundaries.py
tests/unit/test_main_assistant_entrypoint.py
tests/integration/test_full_read_workflow.py
tests/integration/test_full_translate_workflow.py
```

## Automated Validation

Run focused Phase 9 tests:

```powershell
python -m pytest tests/unit/test_assistant_state.py
python -m pytest tests/unit/test_assistant_workflow.py
python -m pytest tests/unit/test_assistant_workflow_failures.py
python -m pytest tests/unit/test_assistant_workflow_logging_privacy.py
python -m pytest tests/unit/test_assistant_workflow_scope_boundaries.py
python -m pytest tests/unit/test_main_assistant_entrypoint.py
python -m pytest tests/integration/test_full_read_workflow.py
python -m pytest tests/integration/test_full_translate_workflow.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_assistant_state.py tests/unit/test_assistant_workflow.py tests/unit/test_assistant_workflow_failures.py tests/unit/test_assistant_workflow_logging_privacy.py tests/unit/test_assistant_workflow_scope_boundaries.py tests/unit/test_main_assistant_entrypoint.py tests/integration/test_full_read_workflow.py tests/integration/test_full_translate_workflow.py
```

Run the full unit suite after implementation:

```powershell
python -m pytest tests/unit
```

Run available quality checks:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy .
```

If optional tools are not installed, record that they could not be run and keep
pytest plus ruff as the required validation baseline.

Current validation note for this workspace: `python -m black --check .` and
`python -m mypy .` require optional packages that may not be installed in the
active interpreter. If either command reports `No module named black` or
`No module named mypy`, treat that as an unavailable optional-tool note rather
than a Phase 9 implementation failure.

Check Phase 9 files for unfinished implementation markers before completion.

For command-line smoke checks that must not start live hardware:

```powershell
python main.py --help
python main.py --self-check
python main.py --once "read text"
```

`--once` uses the Phase 9 workflow entrypoint, but it requires injected runtime
boundaries for live behavior. Without those boundaries it should fail safely
with unavailable guidance rather than starting camera, OCR, microphone, TTS, or
translation services during import.

## Manual Acceptance

On target hardware or a documented equivalent test environment:

1. Start the assistant.
2. Issue a supported Arabic read command.
3. Confirm spoken capture guidance is produced.
4. Confirm the assistant selects a best frame, performs OCR, cleans text, and
   starts reading.
5. Issue a translate-to-English command.
6. Confirm latest clean text is translated and the translation is read aloud.
7. Repeat with an English read command followed by translate-to-Arabic.
8. Disable internet or simulate online unavailability and confirm configured
   offline fallback or clear degraded-mode guidance.
9. Trigger operational shutdown and confirm camera/audio resources are released.

During automated development, use mocked camera, OCR, translation, and speech
boundaries. Live hardware and microphone access are optional manual acceptance
inputs, not requirements for importing `main.py` or running unit tests.

Manual hardware acceptance is complete when a documented target device or
equivalent test environment demonstrates both Arabic read-then-translate-to-
English and English read-then-translate-to-Arabic. If hardware, audio output,
local OCR, local translation, or microphone tooling is unavailable, record the
missing dependency and keep the mocked integration tests as the automated
evidence for this phase.

## Acceptance Checklist

- Read command triggers capture, best-frame selection, OCR cascade, cleanup,
  latest-state update, and reading in order.
- Translation commands use latest successful clean text and requested target
  language.
- Additional read commands during an active read workflow return busy guidance
  and start no second capture.
- All rejected capture bursts return spoken recapture guidance and do not
  auto-loop.
- Camera, OCR, cleanup, translation, TTS, timeout, and unexpected failures
  return structured guidance without uncaught exceptions.
- Previous successful clean text and translated text survive recoverable
  failures until replaced or cleared by shutdown.
- Operational shutdown works through process interruption, service stop, or
  test harness control.
- Voice stop remains playback control and is not a new exit command.
- Default logs contain no images, raw OCR text, clean text, translated text,
  command transcripts, speech input, snippets, secrets, or debug artifacts.
- Phase 9 code does not add new engines, command categories, cleanup rules,
  benchmark tooling, deployment services, visual UI, accounts, or cloud storage.
