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
