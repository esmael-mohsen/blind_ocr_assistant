# Architecture

Phase 0 creates an importable scaffold for the future assistive OCR workflow.

## Phase 0 Boundary

Implemented behavior is limited to:

- command help
- bootstrap self-check
- safe configuration defaults
- local operational logging
- common success/failure results
- importable package placeholders

Reserved package areas are present for future phases:

- `modules.camera`
- `modules.image_processing`
- `modules.ocr`
- `modules.text`
- `modules.translation`
- `modules.voice`
- `modules.assistant`

These packages must remain behavior-free in Phase 0. OCR, camera capture,
voice recognition, text-to-speech, translation, and full assistive workflow logic
begin in later phases.

## Phase 1 OCR Engine Layer

Phase 1 implements independent OCR engines behind `modules.ocr.OCRBaseEngine`.
The layer owns:

- `OCRRequest`
- `OCRResult`
- stable OCR error codes
- online OCR engine wrapper
- local accuracy OCR wrapper with lazy loading
- emergency OCR wrapper

Phase 1 still does not implement camera capture, image-quality pre-checking,
best-frame selection, OCR cascade routing, text cleanup, voice commands, TTS, or
translation.

Default OCR logs must contain metadata only: engine name, duration, success
status, and error code. Raw OCR text is excluded unless an explicit debug text
logging path is added later.

## Phase 2 Image Processing Layer

Phase 2 implements local still-image quality checks and preprocessing in
`modules.image_processing`. The layer owns:

- `ImageInput`
- `ImageQualityReport`
- image quality statuses and stable image-processing error codes
- bilingual guidance messages for later spoken feedback
- text-presence estimation without OCR
- `online_light`, `local_natural`, and `emergency_strong` preprocessing variants

Poor or uncertain images are blocked from the normal OCR path with corrective
guidance. Rejected images do not automatically enter preprocessing. Accepted
images may produce the three named OCR-preparation variants while preserving the
original image.

Phase 2 still does not implement camera capture, depth analysis, best-frame
selection, OCR engine execution, OCR cascade routing, text cleanup, voice
commands, TTS playback, or translation.

Default image-processing logs must contain metadata only: statuses, scores,
guidance category, dimensions, variant names, and error codes. Image bytes,
image arrays, OCR text, private document content, and debug artifact paths are
excluded by default.

## Phase 3 Camera Capture and Best-Frame Selection

Phase 3 implements camera capture and deterministic best-frame selection in
`modules.camera`. The layer owns:

- `CaptureRequest` clamped to a 10-20 frame burst, defaulting to 15
- camera source types and stable camera error codes
- target depth camera adapter boundary
- generic OpenCV RGB fallback adapter
- frame candidate models with safe metadata
- depth distance reports for too close, acceptable, too far, and unavailable
- deterministic frame scoring and tie-breaking
- developer camera validation through `scripts/test_camera.py`

The camera source order prefers the target depth camera and falls back to generic
RGB capture when the target camera is unavailable. Automated tests use mocked
sources; live camera validation is opt-in.

Depth is an enhancement, not a requirement. RGB-only mode remains valid when
depth is missing, unsupported, noisy, invalid, or unaligned. Distance guidance
uses the Phase 3 defaults: too close below 25 cm, acceptable from 25 cm through
75 cm, and too far above 75 cm.

Frame selection uses Phase 2 image-quality reports as the primary signal, then
stability and optional distance contributions. Similar scores are resolved
deterministically by acceptable quality, stability, and earliest capture order.
If no acceptable frame exists, the layer returns `NO_ACCEPTABLE_FRAME` with
recapture guidance.

Phase 3 still does not implement OCR execution, OCR cascade routing, text
cleanup, voice commands, TTS playback, translation, or full assistant workflow
orchestration.

Default camera logs must contain metadata only: source type, fallback mode,
frame count, selected frame id, score summaries, distance status, timeout flag,
cleanup status, and failure code. RGB arrays, depth arrays, OCR text, private
document content, and debug artifact paths are excluded by default.

## Phase 4 OCR Cascade Controller

Phase 4 implements OCR quality scoring and cascade routing in `modules.ocr`.
The layer owns:

- `OCRCascadeRequest`
- `OCRCascadeResult`
- `OCRAttempt`
- `OCRCascadeError`
- deterministic `OCRQualityReport` scoring
- normal, offline, and High Accuracy Mode routing
- privacy-preserving cascade log metadata

OCR quality accepts scores at or above `0.70` by default. Empty text, very short
text, symbol-heavy output, repeated characters, excessive spacing, and Arabic
fragmentation lower the quality decision. Arabic, English, mixed, and unknown
language status is detected locally from OCR output.

Normal routing attempts online OCR first, then local accuracy OCR, then
emergency OCR. Weak or failed results fall through to the next engine. If the
selected image is not ready for OCR, the cascade returns
`IMAGE_NOT_READY_FOR_OCR` without calling any OCR engine.

Offline routing is used when online OCR is disallowed, unavailable, or its
availability check times out. In that mode the online engine is skipped without
uploading the image, local accuracy OCR is attempted first, and emergency OCR is
the fallback. Each allowed engine is attempted at most once per cascade request.

High Accuracy Mode compares available online and local accuracy candidates
before choosing. It selects the higher-quality acceptable result, prefers local
accuracy when acceptable scores differ by less than `0.05`, and uses shorter
duration as the final tie-break. Emergency OCR is used only when compared
candidates fail or are too weak.

Phase 4 still does not implement camera capture, best-frame selection, text
cleanup, voice commands, TTS playback, translation, or full assistant workflow
orchestration.

Default cascade logs contain metadata only: attempted path, selected engine,
duration, quality score, fallback use, offline route use, High Accuracy use, and
failure codes. OCR text is excluded unless debug mode and explicit sensitive
text logging are both enabled. Image bytes, uploaded payloads, debug paths,
secrets, raw text, and clean text are excluded by default.

## Phase 5 Text Cleanup, RTL Handling, and Language Detection

Phase 5 implements local text preparation in `modules.text`. The layer owns:

- `TextCleanupRequest`
- `TextCleanupResult`
- `LanguageDetectionResult`
- `DirectionInfo`
- conservative OCR garbage cleanup
- Arabic, English, mixed, and unknown language classification
- RTL, LTR, mixed, and unknown direction metadata
- privacy-preserving text cleanup log metadata

Cleanup preserves raw OCR text exactly and emits a separate clean text value.
It normalizes repeated spaces, tabs, OCR line breaks, and punctuation spacing
while preserving paragraph boundaries, list-like breaks, Arabic punctuation,
diacritics, numbers, dates, prices, symbols, and mixed Arabic/English segments.
Uncertain fragments are preserved with warnings instead of being deleted.

Language detection is deterministic and offline. Dominant Arabic or English
requires enough language-bearing evidence and at least 60 percent support.
Mixed language requires meaningful Arabic and English evidence. Empty,
symbol-heavy, very short, or insufficient-evidence text returns unknown rather
than a false dominant language.

RTL handling preserves logical reading order for later speech and translation.
The text layer does not reverse Arabic strings into display-only visual order.
Direction metadata identifies RTL, LTR, mixed, or unknown content.

Phase 5 still does not implement OCR execution, camera capture, image
processing, translation, voice commands, TTS playback, or full assistant
workflow orchestration.

Default text logs contain metadata only: status, language, direction, warning
codes, raw length, clean length, and source engine. Raw text and clean text are
excluded unless debug mode and explicit sensitive-text logging are both enabled.

## Phase 6 TTS Reading Controller

Phase 6 implements local text-to-speech reading in `modules.voice`,
deterministic reading segmentation in `modules.text`, and reading state in
`modules.assistant`. The layer owns:

- `SpeechRequest`
- `SpeechResult`
- `TTSError`
- `TextSegment`
- `ReadingControlCommand`
- `ReadingState`
- `TTSEngine`
- `EspeakNGEngine`
- `ReadingController`

The reading controller accepts clean text from Phase 5 or equivalent tests and
passes that text to a replaceable TTS engine boundary. The initial live adapter
uses local eSpeak NG through a subprocess boundary, while automated tests use a
mock TTS engine.

The MVP read-aloud path supports Arabic, English, and mixed clean text in the
logical order supplied by Phase 5. Empty or whitespace-only text is not spoken
and returns `NO_READABLE_TEXT` guidance. Failed TTS requests return structured
results and leave the reading state inactive.

Playback controls are stateful and visual-free. Stop is idempotent, native pause
and resume are used when supported, and unsupported pause/resume degrades by
stopping safely and replaying the current segment on continue. Speech rates
default to 150 words per minute and are clamped to 80 through 220 words per
minute before reaching the engine.

Sentence and paragraph segmentation is deterministic. Paragraphs split on blank
lines; sentences split on Arabic and English sentence-ending punctuation. When
exact speech progress is unknown, repeat history uses the first current logical
sentence or paragraph rather than guessing later text. Repeat failures return
`NOTHING_TO_REPEAT` guidance without speaking unrelated content.

Phase 6 still does not implement camera capture, OCR execution, image
processing, text cleanup, translation, voice command parsing, or full assistant
workflow orchestration.

Default TTS logs and safe metadata contain operation names, engine names,
success status, duration when available, rate, fallback use, error category, and
segment identifiers. Raw OCR text, clean text, spoken text, sentence snippets,
and paragraph snippets are excluded by default.
