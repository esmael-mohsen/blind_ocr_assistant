# Phase 8 Contract: Voice Assistant Command System

## Scope

This contract defines internal Python-facing behavior for Phase 8 command
recognition and command routing. It covers command models, deterministic fixed
command parsing, online STT boundary, local Vosk fallback boundary, dialogue
manager routing, spoken guidance, latest-only state, and privacy behavior.

It does not define camera capture, OCR execution, image processing, text
cleanup, translation execution, TTS engine behavior, or full assistant
orchestration.

## Command Parser Contract

The parser must expose behavior equivalent to:

```python
class CommandParser:
    def parse(self, request: CommandRequest) -> CommandResult: ...
```

### Requirements

- Accept Arabic and English command phrases from a curated fixed catalog.
- Normalize harmless transcript variation such as casing, spacing,
  punctuation, and simple Arabic diacritics.
- Return a single supported action intent only when exactly one intent is
  confidently matched.
- Return `UNKNOWN_COMMAND` or `AMBIGUOUS_COMMAND` guidance when no safe command
  can be routed.
- Never include raw phrase text or snippets in safe metadata.

## Recognizer Boundary Contract

Recognizers must expose behavior equivalent to:

```python
class CommandRecognizer:
    name: str
    path: str

    def recognize(self, request: CommandRequest) -> CommandResult: ...
```

### Online STT Boundary

The online boundary must:

- Be optional, free or replaceable, and disabled by default unless configured.
- Respect `allow_online=false` by returning unavailable without sending speech
  or transcript content.
- Convert timeout, unconfigured service, malformed response, no-supported-command
  output, and provider failure into structured results.
- Provide safe metadata only.

### Local Vosk Fallback Boundary

The local fallback must:

- Be usable for fixed commands when online recognition is unavailable or fails.
- Lazy-load optional local resources.
- Return unavailable failure when package or model resources are missing.
- Use the same structured result shape as the online boundary.

## Dialogue Manager Contract

The dialogue manager must expose behavior equivalent to:

```python
class DialogueManager:
    def handle_command(
        self,
        phrase: str,
        language_hint: str = "unknown",
        allow_online: bool = True,
        allow_local: bool = True,
    ) -> CommandResult: ...

    def get_state(self) -> DialogueState: ...
```

### Operation Guarantees

- Empty or noise-only command input returns `NO_COMMAND_INPUT` and does not
  route any action.
- Online recognition is attempted first when allowed and available.
- Local fixed-command fallback is attempted when online recognition is disabled,
  unavailable, timed out, failed, or returns no supported command.
- Unknown, ambiguous, low-confidence, and help results do not route reading,
  translation, capture, OCR, or cleanup.
- Read commands route to the existing reading behavior only when latest clean
  text is available.
- Stop, continue, repeat sentence, and repeat paragraph route to the existing
  reading behavior and handle missing reading state with guidance.
- Translation commands route to the existing translation behavior using latest
  clean text and the requested target language.
- Routing failures return structured guidance and do not crash the assistant.
- Latest command state stores only safe metadata and guidance.

## Privacy Contract

Default logs and safe metadata may include:

- operation name
- recognizer name
- selected path
- command language
- command intent
- confidence category
- fallback used
- route status
- error category
- duration

Default logs and safe metadata must not include:

- raw speech input
- recognized phrase text
- command phrase snippets
- raw OCR text
- clean text
- translated text
- provider secrets or endpoint credentials

## Scope Boundaries

Phase 8 tests must assert that command-system code does not call camera capture,
OCR cascade execution, image processing, text cleanup, translation execution,
TTS engine implementation, or full assistant workflow orchestration.
