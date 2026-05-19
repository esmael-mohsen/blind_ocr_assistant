# Phase 8 Data Model: Voice Assistant Command System

## CommandRequest

Represents one spoken or transcript-level command attempt.

**Fields**:
- `phrase`: Recognized phrase or test-provided command text.
- `language_hint`: `ar`, `en`, `mixed`, or `unknown`.
- `allow_online`: Whether online recognition may be attempted.
- `allow_local`: Whether local fixed-command fallback may be attempted.
- `operation`: Command operation context.

**Validation rules**:
- Empty, whitespace-only, silence-only, or noise-only input must not route an
  action.
- Phrase text must not appear in default logs or safe metadata.
- Online recognition cannot be required for fixed commands.

## CommandIntent

Represents the classified user intention.

**Values**:
- `read`
- `stop`
- `continue`
- `repeat_sentence`
- `repeat_paragraph`
- `translate_to_arabic`
- `translate_to_english`
- `help`
- `unknown`
- `ambiguous`

**Validation rules**:
- Exactly one supported action intent is required before routing.
- `unknown`, `ambiguous`, and `help` do not trigger reading or translation.
- Capture workflow intents are out of scope for Phase 8.

## CommandResult

Represents the outcome of command recognition and optional routing.

**Fields**:
- `success`: Whether a supported intent was recognized and, when applicable,
  routed successfully.
- `intent`: Classified command intent.
- `language`: Effective command language.
- `path`: `online`, `local`, or `parser`.
- `fallback_used`: Whether local fallback was used after online recognition
  could not produce a supported command.
- `confidence`: `high`, `low`, `ambiguous`, or `none`.
- `target_language`: `ar` or `en` for translation commands.
- `routed`: Whether an action was handed to reading or translation behavior.
- `routed_success`: Whether the routed behavior succeeded.
- `error`: Optional `CommandError`.
- `guidance`: User-safe spoken guidance.

**Validation rules**:
- Failure or non-routed results must include guidance.
- Low-confidence or multi-intent results must not route an action.
- Phrase text must be excluded from safe metadata.

## CommandRecognizer

Represents a replaceable recognition boundary.

**Fields**:
- `name`: Recognizer name.
- `path`: `online` or `local`.
- `supports_languages`: Supported command languages.

**Behavior rules**:
- Returns `CommandResult` or structured failure.
- Must not raise recognizer exceptions to the dialogue manager.
- Must expose safe metadata only.
- Local recognition resources must be lazy-loaded.

## CommandError

Represents stable command failure categories.

**Initial error codes**:
- `NO_COMMAND_INPUT`
- `UNKNOWN_COMMAND`
- `AMBIGUOUS_COMMAND`
- `LOW_CONFIDENCE_COMMAND`
- `ONLINE_STT_UNAVAILABLE`
- `ONLINE_STT_FAILED`
- `LOCAL_STT_UNAVAILABLE`
- `LOCAL_STT_FAILED`
- `ROUTING_TARGET_UNAVAILABLE`
- `COMMAND_ROUTING_FAILED`
- `ALL_RECOGNIZERS_FAILED`

## DialogueState

Represents latest-only safe command state.

**Fields**:
- `last_intent`: Latest classified command intent.
- `selected_path`: `online`, `local`, or `parser`.
- `fallback_used`: Whether local fallback was used.
- `last_result`: Latest structured command result without phrase text in safe
  metadata.
- `last_guidance`: Latest user-safe guidance.

**State transitions**:
- Recognized commands replace the previous latest command state.
- Unknown, ambiguous, low-confidence, and failed commands replace only safe
  command feedback state and do not change reading or translation state.
- Raw speech and recognized phrase text are discarded after classification.

## CommandFeedback

Represents spoken confirmation or recovery guidance.

**Fields**:
- `guidance`: User-safe guidance text.
- `intent`: Intent associated with guidance.
- `requires_action`: Whether guidance follows a routed command.
- `examples_available`: Whether help examples can be offered.

**Validation rules**:
- Guidance must be present for every result.
- Help feedback must not route reading, translation, capture, OCR, or cleanup.
