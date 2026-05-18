# Phase 6 Contract: TTS Reading Controller

## Scope

This contract defines the internal Python interfaces for Phase 6. It covers the
TTS engine boundary, deterministic text segmentation, and reading controller
operations. It does not define OCR, camera, text cleanup, translation, voice
command parsing, or full assistant orchestration behavior.

## TTS Engine Boundary

Implementations must expose behavior equivalent to this protocol:

```python
class TTSEngine:
    name: str
    supports_pause: bool
    supports_resume: bool

    def speak(self, request: SpeechRequest) -> SpeechResult: ...
    def stop(self) -> SpeechResult: ...
    def pause(self) -> SpeechResult: ...
    def resume(self) -> SpeechResult: ...
```

### Requirements

- `speak` must receive clean text only.
- `speak` must return structured success or failure and must not raise
  subprocess, engine, or environment errors to the controller.
- `stop` must be safe when no speech is active.
- `pause` and `resume` may return unsupported results. The controller owns the
  fallback behavior.
- Engine adapters must expose safe metadata: engine name, operation, duration,
  rate, success/failure, and error category.
- Engine adapters must not log raw OCR text, clean text, spoken text, or segment
  snippets by default.

## eSpeak NG Adapter Contract

The initial adapter must:

- Use a local eSpeak NG command boundary.
- Map `ar`, `en`, and `mixed` language metadata to available eSpeak NG voice
  arguments conservatively.
- Apply the clamped `rate_wpm` from `SpeechRequest`.
- Convert missing binary, non-zero exit, timeout, and process errors into
  structured `TTSError` results.
- Be testable with subprocess calls mocked.

Live audio output is validated through `scripts/test_tts.py` when eSpeak NG is
available. Automated tests must not require live audio hardware.

## Segmentation Contract

The segmentation module must expose behavior equivalent to:

```python
def split_paragraphs(text: str, language: str = "mixed") -> list[TextSegment]: ...
def split_sentences(text: str, language: str = "mixed") -> list[TextSegment]: ...
```

### Requirements

- Paragraphs split on blank-line boundaries.
- Sentences split on Arabic and English sentence-ending punctuation.
- Logical text order from Phase 5 is preserved.
- Empty segments are discarded.
- Segment identifiers are stable within a current text identity.
- Segment text is never emitted in default logs.

## Reading Controller Contract

The controller must expose behavior equivalent to:

```python
class ReadingController:
    def start_reading(
        self,
        clean_text: str,
        language: str = "mixed",
        rate_wpm: int | None = None,
    ) -> SpeechResult: ...

    def stop(self) -> SpeechResult: ...
    def pause(self) -> SpeechResult: ...
    def continue_reading(self) -> SpeechResult: ...
    def set_rate(self, rate_wpm: int) -> SpeechResult: ...
    def repeat_last_sentence(self) -> SpeechResult: ...
    def repeat_last_paragraph(self) -> SpeechResult: ...
    def get_state(self) -> ReadingState: ...
```

### Operation Guarantees

- `start_reading` rejects empty or whitespace-only text without calling the
  speech engine.
- `start_reading` updates reading state only after a successful speech request.
- `stop` leaves the controller inactive and is idempotent.
- `pause` uses native engine pause when available.
- `pause` fallback stops speech safely, preserves the current segment, and
  returns guidance explaining the fallback.
- `continue_reading` resumes natively when available or replays the current
  segment after fallback.
- `set_rate` clamps to 80-220 words per minute and affects future speech
  requests.
- `repeat_last_sentence` speaks only the last successfully requested sentence
  when available.
- `repeat_last_paragraph` speaks only the last successfully requested paragraph
  when available.
- Repeat without history returns guidance and does not speak unrelated text.
- TTS failure leaves reading inactive and preserves prior successful repeat
  history.

## Privacy Contract

Default logs and safe metadata may include:

- operation name
- engine name
- result status
- duration
- clamped rate
- fallback used
- error category
- segment type and order

Default logs and safe metadata must not include:

- raw OCR text
- clean text
- spoken text
- sentence snippets
- paragraph snippets

## Scope Boundaries

Phase 6 tests must assert that the controller does not import or call camera
capture, OCR cascade execution, OCR cleanup, translation engines, STT, command
parsing, or full assistant dialogue orchestration.
