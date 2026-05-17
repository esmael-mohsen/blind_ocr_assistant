# Troubleshooting

Phase 0 requires no camera, audio device, internet connection, OCR engine, or
translation service.

## Self-Check Reports Missing Quality Tools

Missing `black` or `mypy` is non-blocking in Phase 0. Install optional quality
tools later if you want to run every local check.

## Runtime Folders Are Missing

Run:

```bash
python main.py --self-check
```

The self-check creates `logs/`, `debug_captures/`, `benchmark_results/`, and
`config/` when they are absent.

## OCR or Camera Is Not Available

That is expected in Phase 0. OCR, camera capture, audio, STT, TTS, translation,
and the full assistive workflow are intentionally deferred.

## Online OCR Credential Is Missing

Phase 1 live online OCR checks are opt-in. Without `OCR_SPACE_API_KEY`, live
tests should skip and local tests should still pass.

## Local Accuracy OCR Model Cannot Load

The local accuracy OCR engine returns `OCR_MODEL_LOAD_ERROR` when the optional
package or model cannot load. Importing the project and running bootstrap help
must not load the heavy model.

## Emergency OCR Is Missing

The emergency OCR engine returns `OCR_EXECUTABLE_NOT_FOUND` when Tesseract is not
installed and `OCR_LANGUAGE_DATA_MISSING` when Arabic or English language data is
not available.

## OCR Finds No Text

Empty or weak OCR output is returned as `NO_TEXT_DETECTED` or `WEAK_OCR_RESULT`,
not as successful OCR.
