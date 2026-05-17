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

## Image Is Too Dark Or Too Bright

Phase 2 returns image-quality guidance instead of running OCR. Improve lighting,
avoid glare, and recapture before sending the image to later OCR phases.

## Image Is Blurry

Phase 2 returns steadiness or recapture guidance. Hold the camera steady and try
again before OCR is attempted.

## Image Has Low Contrast

Phase 2 classifies low contrast separately from dark or blurry input. Move the
document to clearer contrast or better lighting, then recapture.

## No Text-Like Region Is Found

Phase 2 blocks unlikely-text images and returns point-to-text guidance. The
text-presence estimator is local and does not run OCR.

## Image Format Is Unsupported

Missing, empty, unreadable, or unsupported image input returns a structured
image-processing error instead of crashing.

## Rejected Image Was Not Preprocessed

That is expected in the normal Phase 2 workflow. Rejected or uncertain images
return corrective guidance first; preprocessing variants are produced only after
an accepted quality report.
