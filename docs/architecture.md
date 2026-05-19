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

## Phase 7 Translation Layer

Phase 7 implements Arabic/English translation in `modules.translation` and
stateful translation routing in `modules.assistant.translation_controller`.
The MVP accepts clean text from Phase 5 or equivalent tests, translates between
Arabic and English through a replaceable engine boundary, and hands successful
translated output to the Phase 6 reading controller when that boundary is
available.

The translation controller preserves source clean text separately from
translated text, keeps only the latest successful translation in memory, and
returns structured guidance for no readable text, provider failure, invalid
translation output, and successful reading handoff.

Online translation is attempted first when allowed, and local Argos Translate is
used as a lazy-loaded fallback when the online path is disabled, unavailable,
failed, timed out, or returned invalid output. Same-language requests are
successful no-op results that avoid provider calls and preserve the clean text
for reading.

Phase 7 still does not implement camera capture, OCR execution, image
processing, text cleanup, voice command parsing, or full assistant workflow
orchestration.

Default translation logs and safe metadata contain operation names, provider
names, source and target language codes, selected path, duration, fallback use,
validity status, reading handoff status, error category, and text lengths. Raw
OCR text, clean text, translated text, source snippets, translated snippets,
provider secrets, and endpoint credentials are excluded by default.

## Phase 8 Voice Assistant Command System

Phase 8 implements fixed Arabic and English voice command recognition in
`modules.voice` and command routing in `modules.assistant.dialogue_manager`.
The MVP recognizes read commands, playback controls, translation commands, and
help. It routes read and playback commands to the existing reading controller
when the required state is available, and routes translate-to-Arabic or
translate-to-English commands to the existing translation controller using the
latest clean text.

Command recognition is online-first when an online recognizer is configured and
allowed. Disabled, unavailable, timed-out, failed, or no-supported-command
online results may fall back to the local fixed-command recognizer. Local Vosk
resources are lazy-loaded, and missing packages or models return structured
unavailable results.

Help returns supported examples without routing reading, translation, capture,
OCR, cleanup, image processing, TTS engine, or workflow actions. Translation
commands require latest clean text and an injected translation boundary;
otherwise they return spoken recovery guidance.

The dialogue manager keeps only latest safe command metadata and guidance.
Raw speech text, recognized phrase text, command snippets, raw OCR text, clean
text, and translated text are excluded from default command logs and safe
metadata.

Phase 8 still does not implement camera capture, OCR execution, image
processing, text cleanup, translation execution, TTS engine implementation, or
full assistant workflow orchestration. It only recognizes fixed commands and
hands off to injected boundaries from earlier phases.

## Phase 9 Full Assistive Workflow Integration

Phase 9 implements the full assistant workflow coordinator in
`modules.assistant.workflow` and latest in-memory workflow state in
`modules.assistant.state`. The coordinator owns orchestration only: command
routing, capture handoff, best-frame selection handoff, OCR cascade handoff,
text cleanup handoff, reading handoff, translation handoff, recoverable failure
mapping, single-active-read protection, and operational shutdown.

The workflow coordinator depends on injected boundaries from earlier phases
instead of concrete provider internals. Camera capture, frame selection, OCR
engines, cleanup rules, TTS engines, translation engines, and command
recognizers remain owned by their existing modules. Importing `main.py` creates
no live hardware, microphone, camera, OCR, translation, or speech side effects.

The read workflow runs in this order:

- recognized read command
- bounded capture burst
- best-frame selection or capture-provided selection result
- OCR cascade on the selected frame
- text cleanup on OCR output
- reading controller handoff with detected language
- latest successful read state update

The translation workflow uses only the latest successful clean text. It routes
translate-to-Arabic and translate-to-English requests to the injected
translation controller, stores the latest successful translated text, and
preserves previous successful read or translation state when a later attempt
fails.

Assistant state is latest-only and volatile. It may hold latest raw OCR text,
latest clean text, latest translated text, detected language, selected OCR
engine, fallback flags, current mode, and last guidance while the process is
running. Shutdown clears text-bearing in-memory state and leaves a final
shutdown status.

Recoverable workflow failures use stable `WorkflowFailure` categories for busy
workflow, missing command/camera/OCR/cleanup/TTS/translation boundaries, capture
timeout, no acceptable frame, OCR failure, cleanup-empty text, translation
failure, component timeout, unexpected boundary failure, resource-release
failure, and shutdown requested. Failed read or translation attempts preserve
previous successful clean text and translated text until replaced by a later
success or cleared by shutdown.

Operational shutdown is separate from voice stop. Voice stop remains a reading
playback command, while shutdown is triggered by process interruption, service
stop, or test-harness control. Shutdown stops active speech when possible,
runs injected cleanup hooks, clears volatile text state, and prevents new read
or translation work.

Default Phase 9 safe metadata contains only operational facts such as status,
mode, language, selected OCR engine, fallback use, duration, boundary source,
and error code. Images, depth maps, raw OCR text, clean text, translated text,
command transcripts, speech input, snippets, provider secrets, endpoint
credentials, and debug artifact paths are excluded by default.
## Phase 10 Benchmark Package

`modules.benchmark` is a maintainer-facing package for local OCR measurement.
It is separate from the live assistant workflow and does not import assistant,
voice, translation, camera-loop, or TTS orchestration code.

Dataset lifecycle:

- Safe controlled fixtures live under `tests/benchmark/`.
- `manifest.json` declares local sample paths, language labels, scenario
  labels, quality labels, privacy classification, and expected-text references.
- The loader validates minimum sample count, required coverage, local paths,
  unique sample IDs, expected-text coverage, and safe expected-text fixtures.

Result lifecycle:

- Each run creates a timestamped directory under `benchmark_results/`.
- `results.json`, `summary.json`, and `known_failures.md` are written without
  overwriting prior result sets.
- Default output contains labels, path names, durations, text lengths, scores,
  failure categories, and safe metadata only.

Tuning recommendation lifecycle:

- Benchmark failures can produce evidence-based recommendations for image
  quality, OCR quality, preprocessing, or frame selection.
- Recommendations are serialized as evidence and remain unaccepted by default.
- Acceptance requires measured evidence, documented tradeoffs, and no normal
  Arabic, English, or mixed regression.

Privacy behavior:

- Default benchmark artifacts exclude image payloads, raw OCR text, clean text,
  translated text, provider secrets, endpoint credentials, and private debug
  paths.

## Phase 11 Raspberry Pi Deployment Hardening

Phase 11 adds deployment readiness checks, diagnostics, privacy-safe local
reports, log retention guidance, and optional service assets. Deployment code
lives in `modules.deployment` and verifies existing assistant behavior without
adding OCR, translation, STT, TTS, command, account, cloud, paid-service, or
visual UI features.

The package owns only deployment-facing contracts:

- canonical readiness statuses
- privacy-safe readiness reports
- log retention calculations for normal logs
- disabled-by-default service asset inspection
- lightweight startup and explicit maintainer diagnostics

Deployment checks may inspect availability through existing module boundaries,
but they must not introduce new engines or eagerly load heavy OCR models during
startup. Generated `deployment_diagnostics/` output is ignored by git because it
is local operational evidence.

Service lifecycle:

- `scripts/run_assistant.sh` remains the primary manual startup path.
- `deploy/blind-ocr-assistant.service.template` is optional and disabled until a
  maintainer copies and enables it intentionally.
- Service asset validation checks for explicit stop behavior and warns when
  service startup is already enabled.
- Log retention helpers calculate normal log usage and produce rotate/prune
  decisions without touching debug captures or private artifacts.

Privacy/resource review:

- Deployment report writing rejects sensitive payload keys and omits raw user
  content from JSON and Markdown summaries.
- Lightweight startup checks do not load heavy OCR models, capture images, or
  record audio.
- Full diagnostics can verify heavy/local resources only when explicitly run by
  a maintainer.
- Normal log budgeting defaults to 50 MB and produces prune decisions for normal
  log files only.
- Service startup remains opt-in and disabled by default.
