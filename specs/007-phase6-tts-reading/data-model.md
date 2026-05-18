# Phase 6 Data Model: TTS Reading Controller

## SpeechRequest

Represents a single request to speak text through a TTS engine.

**Fields**:
- `text`: Clean text or a clean segment to speak. Required and non-empty after
  trimming for speak operations.
- `language`: Supported language code, currently `ar`, `en`, or `mixed`.
- `rate_wpm`: Speech rate after clamping. Defaults to 150 and must be within
  80-220.
- `operation`: Operation that produced the request, such as `read_all`,
  `continue`, `repeat_sentence`, `repeat_paragraph`, or `guidance`.
- `segment_id`: Optional stable identifier for the sentence or paragraph being
  spoken.
- `segment_type`: Optional segment type: `sentence`, `paragraph`, or `full_text`.
- `segment_order`: Optional zero-based order within the current text.

**Validation rules**:
- Empty or whitespace-only text must not create an engine speak call.
- Rate values below 80 clamp to 80; values above 220 clamp to 220.
- Text content must not be included in default logs or safe metadata.

## SpeechResult

Represents the outcome of a TTS engine operation.

**Fields**:
- `success`: Whether the engine operation completed as requested.
- `operation`: Operation attempted.
- `engine_name`: Name of the selected engine, such as `espeak_ng` or `mock`.
- `duration_ms`: Optional elapsed duration for observability.
- `error`: Optional `TTSError` when `success` is false.
- `guidance`: User-safe message suitable for spoken feedback.
- `fallback_used`: Whether a degraded behavior was used, such as pause fallback.

**Validation rules**:
- Failure results must include a stable error category and guidance.
- Guidance must not expose raw, clean, or spoken text snippets.
- Engine failures must be represented as structured results, not uncaught
  exceptions.

## ReadingState

Represents the current in-memory reading session.

**Fields**:
- `is_active`: True when reading is currently expected to be audible.
- `is_paused`: True when reading is paused or pause fallback has preserved a
  resume point.
- `current_text_id`: Optional identity for the current clean-text payload.
- `current_segment`: Optional `TextSegment` used as the current resume point.
- `current_rate_wpm`: Current clamped speech rate, default 150.
- `last_sentence`: Last successfully requested sentence segment.
- `last_paragraph`: Last successfully requested paragraph segment.
- `last_operation`: Last control operation attempted.
- `last_result`: Last structured speech result without text content in safe
  metadata.

**State transitions**:
- Start reading with readable text sets `is_active=true`, `is_paused=false`, and
  initializes segments.
- Empty text keeps `is_active=false` and returns guidance without engine calls.
- Stop sets `is_active=false` and `is_paused=false`; it is safe when already
  inactive.
- Native pause sets `is_active=false` and `is_paused=true`.
- Pause fallback stops speech, sets `is_active=false`, keeps the current segment,
  and sets `is_paused=true`.
- Continue from native pause resumes when available; continue after fallback
  replays the current segment with guidance.
- TTS failure sets `is_active=false`, keeps `is_paused=false`, and preserves the
  prior successful repeat history.

## TextSegment

Represents a sentence or paragraph derived from clean text.

**Fields**:
- `segment_id`: Stable identifier derived from current text identity, segment
  type, and order.
- `segment_type`: `sentence` or `paragraph`.
- `order`: Zero-based order in logical reading sequence.
- `text`: Clean segment text.
- `language`: Best available language metadata for the segment.
- `parent_text_id`: Current clean-text payload identity.

**Validation rules**:
- Paragraphs are split by blank lines.
- Sentences are split on Arabic and English sentence-ending punctuation while
  preserving logical order.
- Empty segments are discarded.
- Segment text must not appear in default logs.

## ReadingControlCommand

Represents a playback operation requested by later command routing or tests.

**Fields**:
- `command_type`: `start`, `stop`, `pause`, `continue`, `set_rate`,
  `repeat_sentence`, or `repeat_paragraph`.
- `requested_rate_wpm`: Optional rate for `set_rate` and future speech.
- `language`: Optional requested language metadata.

**Validation rules**:
- Unsupported command types return structured failure.
- `set_rate` clamps rate instead of rejecting recoverable out-of-range values.
- Repeat commands require matching repeat history or return guidance that there
  is nothing to repeat.

## TTSError

Represents stable TTS failure categories.

**Fields**:
- `code`: Stable error code.
- `message`: Developer-safe summary without text content.
- `recoverable`: Whether retry or fallback may succeed.
- `engine_name`: Optional engine associated with the failure.

**Initial error codes**:
- `NO_READABLE_TEXT`
- `TTS_ENGINE_UNAVAILABLE`
- `TTS_ENGINE_FAILURE`
- `TTS_STOP_FAILED`
- `TTS_PAUSE_UNSUPPORTED`
- `TTS_RESUME_UNSUPPORTED`
- `NOTHING_TO_REPEAT`
- `INVALID_COMMAND`
- `UNEXPECTED_TTS_ERROR`

## Relationships

- `ReadingState` owns the active text identity, current segment, and repeat
  history for one reading session.
- `SpeechRequest` may reference a `TextSegment` when speaking a repeat or
  resume segment.
- `SpeechResult` updates `ReadingState` but does not store text in safe
  metadata.
- `ReadingControlCommand` is the input contract for controller operations and
  can be produced by later voice-command routing.
