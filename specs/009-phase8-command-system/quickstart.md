# Phase 8 Quickstart: Voice Assistant Command System

## Purpose

Phase 8 recognizes fixed Arabic and English voice commands, routes supported
commands to existing reading or translation boundaries, and returns spoken
guidance for recognized, unknown, ambiguous, failed, help, and unavailable-state
commands.

## Expected Files

```text
modules/voice/command_models.py
modules/voice/command_parser.py
modules/voice/vosk_fallback.py
modules/voice/stt_online.py
modules/assistant/dialogue_manager.py
tests/unit/test_command_models.py
tests/unit/test_command_parser.py
tests/unit/test_vosk_fallback.py
tests/unit/test_stt_online.py
tests/unit/test_dialogue_manager.py
tests/unit/test_command_logging_privacy.py
tests/unit/test_command_scope_boundaries.py
tests/fixtures/voice/command_phrases.md
```

## Automated Validation

Run focused Phase 8 tests:

```powershell
python -m pytest tests/unit/test_command_models.py
python -m pytest tests/unit/test_command_parser.py
python -m pytest tests/unit/test_vosk_fallback.py
python -m pytest tests/unit/test_stt_online.py
python -m pytest tests/unit/test_dialogue_manager.py
python -m pytest tests/unit/test_command_logging_privacy.py
python -m pytest tests/unit/test_command_scope_boundaries.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_command_models.py tests/unit/test_command_parser.py tests/unit/test_vosk_fallback.py tests/unit/test_stt_online.py tests/unit/test_dialogue_manager.py tests/unit/test_command_logging_privacy.py tests/unit/test_command_scope_boundaries.py
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

## Acceptance Checklist

- Arabic and English read commands are recognized.
- Arabic and English translation commands identify the requested target
  language.
- Stop, continue, repeat sentence, and repeat paragraph commands route to
  reading behavior or return unavailable-state guidance.
- Online unavailable, disabled, timed-out, failed, or no-supported-command cases
  attempt local fixed-command fallback when allowed.
- Unknown, ambiguous, low-confidence, empty, silence-only, and noise-only inputs
  return helpful guidance and do not route actions.
- Help commands return supported examples without routing actions.
- Raw speech and recognized phrase text are discarded after classification.
- Normal state keeps only latest safe command metadata.
- Default logs contain no raw speech text, recognized phrase text, OCR text,
  clean text, translated text, or snippets.
- Phase 8 code does not call camera, OCR, image processing, text cleanup,
  translation execution, TTS engine implementation, or full workflow
  orchestration.
