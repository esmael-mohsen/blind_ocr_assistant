# Phase 7 Contract: Translation Layer

## Scope

This contract defines the internal Python interfaces for Phase 7 translation.
It covers translation models, provider boundaries, translation routing,
result validation, latest-only state, reading handoff, and privacy behavior.
It does not define camera capture, OCR execution, text cleanup, voice command
parsing, or full assistant orchestration.

## Translation Engine Boundary

Implementations must expose behavior equivalent to:

```python
class TranslationEngine:
    name: str
    path: str

    def translate(self, request: TranslationRequest) -> TranslationResult: ...
```

### Requirements

- Providers must receive clean text only.
- Providers must support Arabic-to-English and English-to-Arabic directions or
  return structured unsupported-language failure.
- Providers must convert network, package, model, response, timeout, and service
  failures into structured `TranslationError` results.
- Providers must not raise provider exceptions to the controller.
- Providers must not log raw OCR text, clean text, translated text, or snippets
  by default.
- Offline provider packages or models must be lazy-loaded.

## Online Provider Contract

The online provider must:

- Be free, optional, and replaceable.
- Respect `allow_online=false` by returning an unavailable or skipped result
  without sending text.
- Convert unavailable service, timeout, invalid response, empty result, and
  wrong-language result into structured outcomes the controller can evaluate.
- Provide safe metadata: provider name, duration, path, status, target language,
  fallback eligibility, and error code.

## Offline Provider Contract

The offline provider must:

- Be local and usable when online translation is disabled or unavailable.
- Lazy-load optional translation resources.
- Return unavailable failure when local resources are missing.
- Provide the same structured result shape as the online provider.

## Translation Controller Contract

The controller must expose behavior equivalent to:

```python
class TranslationController:
    def translate_latest(
        self,
        clean_text: str,
        target_language: str,
        source_language: str = "unknown",
        explicit_source_language: bool = False,
        allow_online: bool = True,
        allow_offline: bool = True,
        read_result: bool = True,
    ) -> TranslationResult: ...

    def get_state(self) -> TranslationState: ...
```

### Operation Guarantees

- Empty or whitespace-only text returns `NO_TEXT_TO_TRANSLATE` and does not call
  translation providers.
- Unsupported target or source language returns guidance and does not call
  providers.
- Mixed or unknown source language without explicit source returns
  `LANGUAGE_DIRECTION_REQUIRED` and does not call providers.
- Same-language requests return successful no-op results and do not call
  providers.
- Online path is attempted first when allowed.
- Offline path is attempted when online is disabled, unavailable, fails, times
  out, or returns an invalid result and offline fallback is allowed.
- Result validation requires non-empty output, target-language compatibility
  when detectable, and changed text except for no-op cases.
- All-provider failure returns structured final failure.
- Successful translation updates latest-only state and replaces prior source and
  translated text.
- Reading handoff is attempted by default when a reading boundary is available.
- Reading handoff failure does not invalidate the translated result.

## Privacy Contract

Default logs and safe metadata may include:

- operation name
- provider name
- selected path
- source and target language
- duration
- fallback used
- result validity
- reading handoff status
- error category
- source and translated text lengths

Default logs and safe metadata must not include:

- raw OCR text
- clean text
- translated text
- source snippets
- translated snippets
- provider secrets or endpoint credentials

## Scope Boundaries

Phase 7 tests must assert that translation code does not call camera capture,
OCR cascade execution, image processing, text cleanup, voice command parsing, or
full assistant dialogue orchestration.
