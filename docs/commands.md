# Commands

Phase 0 supports bootstrap help and self-check commands only.

## Help

```bash
python main.py --help
```

Shows the Phase 0 command surface without loading hardware, OCR, voice,
text-to-speech, or translation modules.

## Self-Check

```bash
python main.py --self-check
```

Verifies:

- project imports
- safe configuration defaults
- local runtime folder creation
- local operational logging
- common result helpers
- optional quality-tool status

Missing optional quality tools are warnings, not failures. The command does not
use service credentials, internet, camera hardware, audio devices, OCR engines,
STT, TTS, or translation engines.

## Optional Live OCR Check

Phase 1 live online OCR verification is opt-in. Set a free `OCR_SPACE_API_KEY`
only when you intentionally want to call the online provider, then run the live
OCR test documented in `specs/002-phase1-ocr-engines/quickstart.md`.

Without the credential, live OCR tests are skipped and local tests still pass.
