# Quickstart: Phase 0 Repository Bootstrap

## Prerequisites

- Python 3.10 or newer.
- No camera, audio device, internet connection, OCR engine, translation service,
  or paid-service account is required for Phase 0.

## Setup

```bash
python -m venv .venv
```

Activate the environment for your shell, then install the Phase 0 dependencies:

```bash
python -m pip install -r requirements.txt
```

Create local environment settings from the example if needed:

```bash
cp .env.example .env
```

The default environment must leave debug image saving and sensitive text logging
disabled.

## Verify Bootstrap

Show help:

```bash
python main.py --help
```

Run the self-check:

```bash
python main.py --self-check
```

Expected result:
- Help exits successfully.
- Self-check exits successfully.
- Local runtime folders exist after self-check.
- Missing optional quality tools are reported as non-blocking.
- No OCR, camera, audio, translation, internet, or paid service is used.

## Run Tests

```bash
python -m pytest
```

The Phase 0 test suite should cover imports, configuration defaults, folder
creation, logging setup, Operation Result behavior, entrypoint help, and
bootstrap self-check.

## Phase 0 Boundary

This quickstart verifies only the repository bootstrap. OCR engines, camera
capture, voice recognition, text-to-speech, translation, and the full assistive
workflow are intentionally deferred to later phases.

## Validation Results

Validated on 2026-05-17:

- `python main.py --help`: passed.
- `python main.py --self-check`: passed.
- `python -m pytest`: passed, 14 tests.
- `python -m ruff check .`: passed.
- `python -m black --check .`: optional tool not installed; non-blocking.
- `python -m mypy .`: optional tool not installed; non-blocking.
- Phase 0 boundary scan: passed; no OCR, camera, audio, STT, TTS, translation,
  internet, or paid-service engine imports are required by the bootstrap code.
