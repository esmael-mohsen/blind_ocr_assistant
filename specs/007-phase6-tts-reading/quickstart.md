# Phase 6 Quickstart: TTS Reading Controller

## Purpose

Phase 6 adds local text-to-speech reading for already-clean OCR text. It
provides playback control, speech-rate configuration, sentence and paragraph
repeat behavior, and privacy-safe reading state.

## Expected Files

```text
modules/voice/tts_engine.py
modules/voice/voice_models.py
modules/text/segmentation.py
modules/assistant/reading_controller.py
scripts/test_tts.py
tests/unit/test_tts_models.py
tests/unit/test_tts_engine.py
tests/unit/test_text_segmentation.py
tests/unit/test_reading_controller.py
tests/unit/test_tts_logging_privacy.py
tests/unit/test_tts_scope_boundaries.py
tests/unit/test_tts_script.py
tests/fixtures/text/segmentation_cases.md
```

## Automated Validation

Run the focused Phase 6 tests:

```powershell
python -m pytest tests/unit/test_tts_models.py
python -m pytest tests/unit/test_tts_engine.py
python -m pytest tests/unit/test_text_segmentation.py
python -m pytest tests/unit/test_reading_controller.py
python -m pytest tests/unit/test_tts_logging_privacy.py
python -m pytest tests/unit/test_tts_scope_boundaries.py
python -m pytest tests/unit/test_tts_script.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_tts_models.py tests/unit/test_tts_engine.py tests/unit/test_text_segmentation.py tests/unit/test_reading_controller.py tests/unit/test_tts_logging_privacy.py tests/unit/test_tts_scope_boundaries.py tests/unit/test_tts_script.py
```

Run the full unit suite after the phase is implemented:

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
the pytest and ruff results as the required validation baseline.

## Manual eSpeak NG Smoke Test

When eSpeak NG and audio output are available on the machine:

```powershell
python scripts/test_tts.py --text "Hello from the Blind OCR Assistant" --language en
python scripts/test_tts.py --text "مرحبا من مساعد القراءة" --language ar
python scripts/test_tts.py --text "Read a little slower" --language en --rate 120
```

The script must report structured success or a structured unavailable-engine
failure. It must not print raw OCR text, clean text, or spoken snippets in
normal logs.

The script writes JSON with safe metadata only: success state, operation, engine
name, duration, fallback flag, and error code. It does not echo the supplied
text.

## Acceptance Checklist

- Arabic and English clean text are sent to the speech engine in mocked tests.
- Empty and whitespace-only text do not call the speech engine.
- Stop is safe when reading is active or inactive.
- Pause and continue update reading state; unsupported native pause/resume uses
  the stop-and-replay fallback.
- Speech rate defaults to 150 words per minute and clamps to 80-220.
- Sentence and paragraph segmentation supports Arabic, English, and mixed text
  fixture samples.
- Repeat last sentence and repeat last paragraph speak only the tracked segment.
- TTS failures return structured guidance, leave reading inactive, and preserve
  prior successful repeat history.
- Default logs contain safe metadata only.
- Phase 6 code does not call camera, OCR, cleanup, translation, STT, command
  parser, or full workflow orchestration.
