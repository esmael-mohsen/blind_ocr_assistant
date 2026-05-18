# Data Model: Phase 5 Text Cleanup, RTL Handling, and Language Detection

## TextCleanupRequest

Represents one raw OCR text payload to prepare for reading and translation.

**Fields**

- `raw_text`: Original OCR text. Preserved exactly in result output.
- `language_hints`: Optional prior hints such as Arabic, English, mixed, or
  unknown.
- `source_engine`: Optional OCR engine name for safe metadata only.
- `preserve_paragraphs`: Whether blank-line paragraph boundaries should be
  preserved. Default true.
- `sensitive_text_logging_enabled`: Explicit opt-in flag for debug-only text
  logging.

**Validation**

- `raw_text` may be empty, but empty input must return a structured empty
  result rather than raising an unhandled exception.
- Request validation must not log raw text.
- Language hints outside Arabic, English, mixed, or unknown are ignored or
  reported as a non-fatal warning.

## TextCleanupResult

Represents the final cleanup outcome.

**Fields**

- `success`: Whether cleanup completed without invalid input failure.
- `raw_text`: Exact original text from the request.
- `clean_text`: Cleaned text prepared for later reading and translation.
- `status`: `clean`, `empty`, `noisy`, `uncertain_language`, or `invalid_input`.
- `language`: Arabic, English, mixed, or unknown.
- `direction`: RTL, LTR, mixed, or unknown.
- `warnings`: Ordered cleanup warnings.
- `guidance`: User-safe message suitable for later spoken feedback.
- `safe_metadata`: Text-free metadata safe for logs.

**Validation**

- `raw_text` must match the request exactly.
- `clean_text` must be idempotent: cleaning it again returns the same clean
  text.
- Successful non-empty results must include language and direction values.
- Empty results must use unknown language and unknown direction.
- Default safe metadata must not include raw or clean text.

## LanguageDetectionResult

Represents deterministic language classification for cleaned text.

**Fields**

- `language`: Arabic, English, mixed, or unknown.
- `confidence`: Numeric evidence score from 0.0 to 1.0.
- `arabic_character_count`: Count of Arabic language-bearing characters.
- `english_character_count`: Count of English language-bearing characters.
- `language_character_count`: Count of all language-bearing characters.
- `dominant_ratio`: Ratio used for dominant Arabic or English decisions.
- `direction`: RTL, LTR, mixed, or unknown.
- `warnings`: Non-fatal language warnings.

**Validation**

- Dominant Arabic or English requires enough language-bearing evidence and at
  least 60% support for that language.
- Mixed requires meaningful evidence for both Arabic and English.
- Empty, symbol-heavy, or insufficient-evidence text returns unknown.
- Direction must align with language where possible: Arabic tends RTL, English
  tends LTR, mixed tends mixed.

## CleanupWarning

Represents a non-fatal concern found during cleanup.

**Values**

- `EMPTY_INPUT`
- `NOISY_TEXT`
- `UNCERTAIN_LANGUAGE`
- `MIXED_DIRECTION`
- `PRESERVED_UNCERTAIN_FRAGMENT`
- `UNSUPPORTED_LANGUAGE_HINT`
- `PUNCTUATION_NORMALIZED`
- `LINE_BREAKS_NORMALIZED`

**Rules**

- Warnings are stable and testable.
- Warnings must not include private text snippets.
- Warnings can drive later spoken guidance without exposing content.

## DirectionInfo

Represents text direction evidence needed by later reading or display workflows.

**Fields**

- `direction`: RTL, LTR, mixed, or unknown.
- `has_rtl`: Whether right-to-left text evidence exists.
- `has_ltr`: Whether left-to-right text evidence exists.
- `logical_order_preserved`: Whether cleanup preserved logical reading order.

**Validation**

- Cleanup must not visually reorder text for display at the expense of logical
  speech or translation order.
- Mixed direction text must preserve all meaningful segments.

## State Transitions

```text
request_received
  -> validate_input
  -> normalize_whitespace_and_line_breaks
  -> normalize_punctuation_spacing
  -> conservative_noise_review
  -> detect_language_and_direction
  -> build_guidance_and_safe_metadata
  -> completed
```

Empty or whitespace-only input transitions from `validate_input` directly to
`completed` with empty status, unknown language, unknown direction, and guidance.
