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

## Camera Is Unavailable

Phase 3 first attempts the target depth camera adapter and then generic RGB
fallback. If neither source opens, the capture result returns
`CAMERA_OPEN_FAILED` with user-safe guidance. Local automated tests still pass
without camera hardware because live camera validation is opt-in.

## Generic RGB Fallback Is Used

RGB fallback is expected when the target depth camera, Orbbec SDK, OpenNI2, or
depth support is unavailable. The system can still capture RGB frames and select
the best frame. Depth status may be recorded as unavailable without failing the
capture.

## Camera Capture Times Out

If at least one valid frame was captured before timeout, Phase 3 scores those
valid frames and records `partial_timeout=true`. If no valid frames were
captured, the result returns `CAMERA_CAPTURE_TIMEOUT` and recapture guidance.

## Camera Returns Empty Or Invalid Frames

Empty frames return `CAMERA_EMPTY_FRAME`. Corrupted or dimensionally invalid
frames return `CAMERA_INVALID_FRAME`. These failures are structured and should
not crash the assistant.

## Depth Is Unavailable Or Noisy

Missing, unsupported, unaligned, invalid, or noisy depth maps return an
unavailable depth report. RGB-only selection continues, and the result preserves
the depth status for later spoken guidance.

## Camera Cleanup Fails

Capture code releases resources after success, failure, timeout, and
cancellation. If release fails, the result can return
`CAMERA_RESOURCE_RELEASE_FAILED`. Restart the camera process or disconnect and
reconnect the camera before retrying live validation.

## Image Is Not Ready For OCR

Phase 4 returns `IMAGE_NOT_READY_FOR_OCR` without calling OCR engines when the
selected image was already rejected by image-quality checks. Improve focus,
lighting, framing, or distance, then recapture before retrying OCR.

## Online OCR Is Unavailable

When online OCR is disabled, unavailable, or its availability check times out,
the cascade skips online OCR and routes locally. This is expected offline
behavior and should not upload the image. Local accuracy OCR runs first, with
emergency OCR as fallback.

## Weak OCR Result

OCR output below the default `0.70` quality threshold is treated as weak even if
the engine returned text. Empty, very short, symbol-heavy, repeated-character,
excessively spaced, or fragmented Arabic output can trigger fallback to the next
engine.

## All OCR Engines Failed

If every allowed engine fails or returns unacceptable text, Phase 4 returns
`ALL_OCR_ENGINES_FAILED` with recapture guidance. Try better lighting, steadier
framing, a flatter page angle, or a closer acceptable distance before retrying.

## High Accuracy Mode Picks The Local Result

High Accuracy Mode may choose local accuracy OCR over online OCR when their
quality scores are similar within `0.05`. This is intentional because local OCR
avoids upload and is preferred for near-tie results.

## Sensitive OCR Text Is Missing From Logs

That is expected by default. Phase 4 logs only safe cascade metadata unless both
debug mode and explicit sensitive-text logging are enabled. Do not enable
sensitive text logging for normal use because OCR text can contain private
document content.

## Clean Text Is Empty

Phase 5 returns an empty cleanup result when OCR text is empty or whitespace
only. This is structured and should be spoken later as no readable text being
available. Recapture or rerun OCR with a clearer image.

## Clean Text Is Marked Noisy

Noisy cleanup means the text may contain uncertain OCR fragments. Phase 5 keeps
those fragments instead of deleting them, because they may be meaningful names,
prices, codes, or mixed-language tokens. Review capture quality or rerun OCR if
the spoken result is unclear.

## Language Is Unknown

Unknown language means there was not enough Arabic or English evidence to make a
safe decision. Empty, very short, symbol-heavy, or mostly numeric text can
produce this result. Later workflows should use safe defaults or ask the user
instead of guessing.

## Mixed Direction Text Is Reported

Mixed direction is expected for bilingual Arabic/English content, receipts,
labels, prices, and product names. Phase 5 preserves logical reading order and
records mixed direction metadata for later reading or display workflows.

## Raw Or Clean Text Is Missing From Logs

That is expected by default. Phase 5 logs only safe metadata unless both debug
mode and explicit sensitive-text logging are enabled. Do not enable sensitive
text logging for normal use because raw and clean OCR text can contain private
document content.

## Local TTS Engine Is Missing

Phase 6 returns `TTS_ENGINE_UNAVAILABLE` when the local eSpeak NG executable is
not installed or cannot be found. Automated tests use a mocked speech engine, so
they still pass without live audio. Install eSpeak NG on the Raspberry Pi or
development machine before running the manual TTS smoke test.

## Reading Does Not Pause Natively

Native pause and resume are not guaranteed for the initial eSpeak NG adapter.
When pause is unsupported, Phase 6 stops speech safely, preserves the current
segment, and reports that continue will replay that segment. This is expected
fallback behavior, not a crash.

## Continue Replays Text Instead Of Resuming Mid-Sentence

If the speech engine does not expose a portable resume point, Phase 6 continues
by replaying the current segment. This avoids guessing ahead when spoken
progress is unknown.

## Stop Is Requested When Nothing Is Reading

Stop is idempotent in Phase 6. It leaves reading inactive and returns structured
guidance even when no speech was active.

## Speech Rate Sounds Too Slow Or Too Fast

Requested rates are clamped to the Phase 6 range of 80 through 220 words per
minute. The default is 150 words per minute. Values outside the range are
accepted but adjusted before future speech requests reach the engine.

## Repeat Says There Is Nothing To Repeat

Phase 6 repeats only tracked sentence or paragraph history. If no clean text has
been read yet, repeat returns `NOTHING_TO_REPEAT` guidance and does not speak
unrelated text. Start reading clean text first, then repeat the sentence or
paragraph.

## TTS Smoke Test Prints JSON Instead Of Text

`scripts/test_tts.py` intentionally prints structured safe metadata only. It
does not echo the supplied text because clean OCR text may contain private
document content.
