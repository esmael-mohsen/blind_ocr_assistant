# Phase 7 Data Model: Translation Layer

## TranslationRequest

Represents a request to translate clean text.

**Fields**:
- `source_text`: Clean text from Phase 5 or equivalent tests.
- `source_language`: `ar`, `en`, `mixed`, or `unknown`.
- `target_language`: `ar` or `en`.
- `allow_online`: Whether the online path may be attempted.
- `allow_offline`: Whether local fallback may be attempted.
- `explicit_source_language`: Whether the caller supplied source language for
  mixed or unknown text.
- `operation`: Translation operation context.

**Validation rules**:
- Empty or whitespace-only text must not call translation providers.
- Source and target language must be supported or return guidance.
- Mixed or unknown source language must not translate unless an explicit
  supported source language is supplied.
- Source text must not appear in default logs or safe metadata.

## TranslationResult

Represents the outcome of a translation operation.

**Fields**:
- `success`: Whether translation completed or a same-language no-op succeeded.
- `source_language`: Effective source language.
- `target_language`: Requested target language.
- `translated_text`: Translated text or preserved clean text for no-op cases.
- `engine_name`: Selected provider or controller path.
- `path`: `online`, `offline`, or `no_op`.
- `fallback_used`: Whether an offline fallback path was used after online could
  not be accepted.
- `duration_ms`: Optional elapsed duration.
- `is_valid`: Whether result passed Phase 7 validity checks.
- `reading_handoff_attempted`: Whether the result was offered to the reading
  layer.
- `reading_handoff_success`: Whether reading handoff succeeded.
- `error`: Optional `TranslationError`.
- `guidance`: User-safe spoken guidance.

**Validation rules**:
- Failure results must include a stable error category and guidance.
- Successful non-no-op results must be non-empty and compatible with the target
  language when detectable.
- Non-no-op results that match the source must be invalid.
- Text fields must be excluded from default logs.

## TranslationEngine

Represents a replaceable provider boundary.

**Fields**:
- `name`: Provider name.
- `path`: `online` or `offline`.
- `supports_languages`: Supported translation directions.

**Behavior rules**:
- Returns `TranslationResult` or provider-level structured failure.
- Must not raise provider exceptions to the controller.
- Must expose safe metadata only.

## TranslationError

Represents stable failure categories.

**Fields**:
- `code`: Stable error code.
- `message`: Developer-safe summary without text content.
- `recoverable`: Whether retry or fallback may succeed.
- `engine_name`: Optional provider associated with failure.

**Initial error codes**:
- `NO_TEXT_TO_TRANSLATE`
- `UNSUPPORTED_LANGUAGE`
- `LANGUAGE_DIRECTION_REQUIRED`
- `TRANSLATION_NOT_NEEDED`
- `ONLINE_TRANSLATION_UNAVAILABLE`
- `ONLINE_TRANSLATION_FAILED`
- `OFFLINE_TRANSLATION_UNAVAILABLE`
- `OFFLINE_TRANSLATION_FAILED`
- `INVALID_TRANSLATION_RESULT`
- `ALL_TRANSLATION_PROVIDERS_FAILED`
- `READING_HANDOFF_FAILED`

## TranslationState

Represents latest-only in-memory translation state.

**Fields**:
- `current_source_text_id`: Stable identity for the latest clean source text.
- `latest_translated_text`: Latest translated text or same-language preserved
  clean text.
- `source_language`: Latest effective source language.
- `target_language`: Latest target language.
- `selected_path`: `online`, `offline`, or `no_op`.
- `fallback_used`: Whether latest result used fallback.
- `reading_handoff_attempted`: Whether reading handoff was attempted.
- `reading_handoff_success`: Whether reading handoff succeeded.
- `last_operation`: Last translation operation.
- `last_result`: Last structured result without text in safe metadata.

**State transitions**:
- Successful translation replaces any previous source and translated text.
- Same-language no-op replaces previous state with preserved clean text.
- Empty, unsupported, or all-provider failure leaves latest successful
  translation state unchanged unless no previous state exists.
- Reading handoff failure does not invalidate a successful translation result.

## TranslationControlRequest

Represents a later user command or test-level translation request.

**Fields**:
- `target_language`: Requested target language.
- `source_language`: Optional explicit source language.
- `allow_online`: Online path permission.
- `allow_offline`: Offline fallback permission.
- `read_result`: Whether successful result should be handed to reading.

**Validation rules**:
- Target language must be Arabic or English.
- Explicit source language must be Arabic or English.
- `read_result` defaults to true when a reading layer is available.

## Relationships

- `TranslationControlRequest` and latest clean text produce a
  `TranslationRequest`.
- `TranslationController` routes `TranslationRequest` through one or more
  `TranslationEngine` implementations.
- `TranslationResult` updates `TranslationState` and may trigger reading
  handoff through the Phase 6 reading boundary.
