# Blind OCR Assistant

Blind OCR Assistant is a voice-first assistive reading project for blind and
visually impaired users. The full system will read Arabic and English printed
text using free online services when available and local open-source fallbacks
when offline.

## Phase 0 Scope

Phase 0 creates the repository bootstrap only. It provides the project scaffold,
configuration defaults, local logging foundation, common result pattern, command
entrypoint, scripts, documentation placeholders, and tests.

Phase 0 intentionally does not implement OCR, camera capture, voice recognition,
text-to-speech, translation, or the full assistive workflow.

## Bootstrap Commands

Show help:

```bash
python main.py --help
```

Run the Phase 0 self-check:

```bash
python main.py --self-check
```

The self-check verifies imports, safe local folders, local logging, common result
helpers, and optional quality-tool status. It does not call hardware, internet,
OCR, camera, audio, translation, STT, TTS, or paid services.

## Hardware Assumptions

The target device for later phases is Raspberry Pi 4 Model B with 4GB RAM and an
Orbbec Astra Pro camera. Phase 0 can run on a development machine without that
hardware.

## Cost and Privacy Policy

No paid service is required. Online credentials are optional and unused during
Phase 0. Debug image saving and sensitive text logging are disabled by default.

Later assistive workflows must provide spoken feedback for all important states;
Phase 0 records that requirement without implementing voice behavior.

## Accessibility Intent

The complete assistant must be usable without visual confirmation. Phase 0 does
not provide the spoken workflow yet, but every later user-facing state must map
to clear spoken feedback.

## Configuration Defaults

`.env.example` documents optional service values for later phases:

- `OCR_SPACE_API_KEY`
- `LIBRETRANSLATE_URL`

Safe defaults:

- `DEBUG_SAVE_IMAGES=false`
- `SENSITIVE_TEXT_LOGGING=false`
- `LOG_LEVEL=INFO`
- `FRAME_CAPTURE_COUNT=15`

The self-check creates local runtime folders when they are missing:

- `logs/`
- `debug_captures/`
- `benchmark_results/`
- `config/`

Phase 0 logs operational bootstrap events only. User images, OCR text,
translations, and voice recordings are not created in this phase.

## Development Checks

Run tests:

```bash
python -m pytest
```

Optional quality commands when installed:

```bash
python -m ruff check .
python -m black --check .
python -m mypy .
```

The bootstrap self-check reports missing optional quality tools as warnings. They
do not block core Phase 0 readiness.

## Raspberry Pi Deployment Hardening

Phase 11 adds a deployment package for Raspberry Pi readiness checks:

```bash
python scripts/pi_deployment_check.py --full --skip-hardware
python scripts/pi_deployment_check.py --full --offline --skip-hardware
```

The diagnostics use Ready, Degraded, Blocked, and Manual Verification Needed
states. They write local privacy-safe summaries under `deployment_diagnostics/`
and exclude user images, OCR text, translations, secrets, and private debug
paths. Manual startup remains available through `scripts/run_assistant.sh`; the
systemd service template is optional and disabled until a maintainer enables it
intentionally.

## Gemini-First OCR

The integrated runtime can use Gemini as the first OCR route for Arabic,
English, and mixed printed text. Configure `GEMINI_API_KEY` and keep
`ASSISTANT_GEMINI_OCR_ENABLED=true` to run Gemini before local OCR. If Gemini is
unavailable, `ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL=true` keeps the assistant
usable through PaddleOCR and Tesseract.

Gemini OCR sends the selected image to the Gemini API. Default logs remain
privacy-safe and exclude image payloads, Base64 data, raw OCR text, cleaned
text, prompts, and secrets.
