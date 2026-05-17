# CLI Contract: Phase 0 Bootstrap Entrypoint

## Purpose

Define the command behavior that proves Phase 0 repository readiness without
invoking OCR, camera, audio, translation, internet, or paid services.

## Commands

### Help

```bash
python main.py --help
```

**Expected behavior**
- Prints usage information.
- Lists the bootstrap self-check command.
- Does not load OCR, camera, audio, voice, TTS, or translation engines.
- Exits with status `0`.

### Bootstrap Self-Check

```bash
python main.py --self-check
```

**Expected behavior**
- Verifies project imports.
- Loads safe configuration defaults.
- Creates local runtime folders when missing:
  - `logs/`
  - `debug_captures/`
  - `benchmark_results/`
  - `config/`
- Initializes local operational logging.
- Verifies the common Operation Result pattern can return success and failure.
- Reports optional quality tooling status for lint, format, and type-check tools
  without failing if those tools are unavailable.
- Does not require service credentials, internet, Raspberry Pi hardware, camera,
  audio, OCR, TTS, STT, or translation packages.
- Exits with status `0` if core bootstrap checks pass.

## Failure Semantics

Core readiness failures use non-zero exit status and a stable error code in the
printed result. Optional quality-tool absence is reported as a warning and does
not change the exit status.

## Privacy Contract

Phase 0 commands must not capture, upload, store, or log user images, OCR text,
translations, or voice recordings. Default logs are limited to operational
bootstrap events.
