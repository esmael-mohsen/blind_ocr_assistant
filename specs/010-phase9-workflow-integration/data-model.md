# Phase 9 Data Model: Full Assistive Workflow Integration

## AssistantSession

Represents one running assistant process.

**Fields**:
- `state`: Current `AssistantState`.
- `workflow_active`: Whether a read workflow is currently running.
- `shutdown_requested`: Whether operational shutdown has been requested.
- `last_result`: Latest workflow result without sensitive content in safe
  metadata.

**Validation rules**:
- Only one read workflow may be active at a time.
- Shutdown prevents new capture, OCR, translation, or reading workflows from
  starting.
- Session state must not persist to disk by default.

## AssistantState

Represents latest in-memory workflow state shared across read, translate, and
playback control behavior.

**Fields**:
- `current_mode`: `idle`, `listening`, `capturing`, `selecting_frame`, `ocr`,
  `cleaning`, `reading`, `translating`, `recovering`, or `shutting_down`.
- `last_raw_text`: Latest successful raw OCR text, in memory only.
- `last_clean_text`: Latest successful clean text, in memory only.
- `last_translated_text`: Latest successful translated text, in memory only.
- `last_language`: `ar`, `en`, `mixed`, or `unknown`.
- `last_ocr_engine`: Selected OCR engine for the latest successful read.
- `fallback_used`: Whether the latest successful workflow used fallback.
- `is_reading`: Whether reading is active according to the reading boundary.
- `is_paused`: Whether reading is paused according to the reading boundary.
- `internet_available`: Latest known internet availability when known.
- `last_guidance`: Latest user-facing spoken guidance.

**State transitions**:
- Successful read replaces `last_raw_text`, `last_clean_text`, `last_language`,
  `last_ocr_engine`, and fallback status.
- Failed read attempts before accepted clean text do not clear prior successful
  clean text.
- Successful translation replaces `last_translated_text`.
- Failed translation does not clear prior successful translated text.
- Shutdown clears in-memory state when the process exits.

## WorkflowRequest

Represents one command-driven or operational workflow request.

**Fields**:
- `request_id`: Stable per-attempt identifier safe for logs.
- `intent`: Read, translate to Arabic, translate to English, playback control,
  help/status, or operational shutdown.
- `language_hint`: Command or content language hint when available.
- `allow_online`: Whether online OCR, translation, or recognition may be used.
- `allow_offline`: Whether offline fallback may be used.
- `high_accuracy`: Whether high-accuracy OCR mode is requested by existing
  configuration or command state.

**Validation rules**:
- Read requests are rejected with busy guidance when a read workflow is already
  active.
- Translation requests require latest successful clean text.
- Shutdown requests can originate from process interruption, service stop, or
  test harness control.

## ReadWorkflowResult

Represents the full outcome of a read workflow.

**Fields**:
- `success`: Whether cleaned text was accepted and reading was requested.
- `capture_success`: Whether a capture burst produced frame candidates.
- `frame_selected`: Whether best-frame selection accepted a frame.
- `ocr_success`: Whether OCR cascade accepted a result.
- `cleanup_success`: Whether cleanup produced readable clean text.
- `reading_started`: Whether the reading controller accepted the clean text.
- `selected_ocr_engine`: Selected OCR engine when successful.
- `fallback_used`: Whether OCR fallback or offline route was used.
- `duration_ms`: Total workflow duration.
- `guidance`: User-facing spoken guidance.
- `error_code`: Stable failure category when unsuccessful.
- `safe_metadata`: Status, duration, fallback, selected engine, and error
  category without image or text payloads.

**Validation rules**:
- Successful result requires accepted clean text and reading handoff.
- Failure result requires guidance and a recoverable or fatal error category.
- Safe metadata must not include image bytes, raw text, clean text, translated
  text, command transcripts, or snippets.

## TranslationWorkflowResult

Represents translation of latest successful clean text.

**Fields**:
- `success`: Whether translation completed and reading handoff was attempted or
  intentionally skipped by the translation boundary.
- `target_language`: `ar` or `en`.
- `source_language`: `ar`, `en`, `mixed`, or `unknown`.
- `translated_text_available`: Whether a successful translated text is present.
- `reading_handoff_attempted`: Whether translated text was sent to reading.
- `reading_handoff_success`: Whether reading accepted translated text.
- `fallback_used`: Whether translation fallback was used.
- `duration_ms`: Total translation workflow duration.
- `guidance`: User-facing spoken guidance.
- `error_code`: Stable failure category when unsuccessful.
- `safe_metadata`: Status, target language, fallback, duration, and error
  category without text payloads.

**Validation rules**:
- Translation requires latest clean text.
- Failure does not clear previous clean text or previous translated text.
- Safe metadata must exclude source text and translated text.

## SpokenStatus

Represents one user-facing spoken message emitted or handed to the speech
boundary.

**Fields**:
- `category`: `confirmation`, `progress`, `fallback`, `success`, `busy`,
  `unavailable`, `recovery`, or `shutdown`.
- `message`: User-facing guidance text.
- `workflow_status`: Associated workflow state.
- `requires_speech`: Whether the coordinator should attempt speech output.

**Validation rules**:
- Every user-facing result must include guidance.
- Status messages must remain short and actionable.

## WorkflowFailure

Represents stable failure categories across integrated boundaries.

**Initial error codes**:
- `WORKFLOW_BUSY`
- `COMMAND_UNAVAILABLE`
- `CAMERA_UNAVAILABLE`
- `CAPTURE_TIMEOUT`
- `NO_ACCEPTABLE_FRAME`
- `IMAGE_NOT_READY_FOR_OCR`
- `OCR_FAILED`
- `NO_TEXT_DETECTED`
- `CLEANUP_EMPTY_TEXT`
- `TRANSLATION_UNAVAILABLE`
- `TRANSLATION_FAILED`
- `TTS_UNAVAILABLE`
- `TTS_FAILED`
- `COMPONENT_TIMEOUT`
- `RESOURCE_RELEASE_FAILED`
- `WORKFLOW_UNEXPECTED_ERROR`
- `SHUTDOWN_REQUESTED`

**Validation rules**:
- Each failure must map to spoken guidance.
- Recoverable failures must keep the assistant responsive.
- Unexpected failures must not expose sensitive content in messages or logs.
