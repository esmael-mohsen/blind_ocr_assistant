# Contract: Phase 5 Text Cleanup Module

## Purpose

Define the public behavior expected from Phase 5 text cleanup, language
detection, RTL handling, and privacy-safe metadata helpers. This is a module
contract for internal assistant workflows and tests, not a network API.

## Cleanup Request Contract

Caller provides:

```text
TextCleanupRequest
- raw_text: str
- language_hints: tuple[str, ...] optional
- source_engine: str optional
- preserve_paragraphs: bool default true
- sensitive_text_logging_enabled: bool default false
```

Contract rules:

- `raw_text` is accepted exactly as produced by OCR.
- Empty and whitespace-only raw text are valid inputs and return structured
  empty results.
- Request handling must not trigger OCR, image processing, translation, TTS,
  voice command parsing, or assistant orchestration.

## Cleanup Result Contract

Cleanup returns:

```text
TextCleanupResult
- success: bool
- raw_text: str
- clean_text: str
- status: clean | empty | noisy | uncertain_language | invalid_input
- language: arabic | english | mixed | unknown
- direction: rtl | ltr | mixed | unknown
- warnings: tuple[CleanupWarning, ...]
- guidance: str
- safe_metadata: dict
```

Contract rules:

- `raw_text` must equal the request raw text exactly.
- `clean_text` must be suitable for later reading and translation.
- Cleanup must be idempotent.
- Ambiguous fragments must be preserved with warnings rather than deleted.
- Default safe metadata must not include raw text, clean text, private snippets,
  secrets, or debug paths.

## Language Detection Contract

Language detection returns:

```text
LanguageDetectionResult
- language: arabic | english | mixed | unknown
- confidence: float
- arabic_character_count: int
- english_character_count: int
- language_character_count: int
- dominant_ratio: float
- direction: rtl | ltr | mixed | unknown
- warnings: tuple[CleanupWarning, ...]
```

Decision rules:

- Dominant Arabic or English requires enough language-bearing evidence and at
  least 60% support for the selected language.
- Mixed requires meaningful Arabic and English evidence.
- Empty, symbol-heavy, or insufficient-evidence text returns unknown.
- Detection must be deterministic for the same input.

## RTL Handling Contract

RTL handling returns logical-order text and direction metadata.

Contract rules:

- Do not reverse Arabic strings for display-only visual ordering.
- Preserve logical reading order for speech and translation inputs.
- Mixed Arabic/English text must preserve all meaningful segments.
- Direction metadata must identify RTL, LTR, mixed, or unknown.

## Privacy Metadata Contract

Default log metadata may include:

```text
- success
- status
- language
- direction
- warning_codes
- raw_length
- clean_length
- source_engine
```

Default log metadata must not include:

```text
- raw_text
- clean_text
- text snippets
- image data
- uploaded payloads
- secrets or tokens
- debug artifact paths
```

Raw or clean text may appear only when both debug mode and explicit
sensitive-text logging are enabled.

## Expected Failure and Guidance Contract

- Empty input: return empty clean text, unknown language, unknown direction, and
  guidance that no readable text was available.
- Noisy input: return best-effort clean text, warnings, and guidance that text
  may be unclear.
- Uncertain language: preserve clean text, return unknown language, and provide
  guidance suitable for asking the user or using a safe default later.
- Invalid input: return structured failure without leaking content.

## Scope Boundary Contract

Phase 5 modules must not import or call:

```text
modules.camera
modules.image_processing
modules.ocr.ocr_cascade
modules.translation
modules.voice
modules.assistant
```

The only allowed relationship to OCR is receiving raw OCR text as input.
