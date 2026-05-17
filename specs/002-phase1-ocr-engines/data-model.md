# Data Model: Phase 1 OCR Engine Prototype

## OCR Engine Interface

Shared contract implemented by each OCR engine.

**Fields / Operations**
- `engine_name`: stable engine identifier.
- `recognize(request)`: accepts one OCR Request and returns one OCR Result.
- `is_available()`: reports whether required credentials, package, executable,
  or language data appear available.

**Validation Rules**
- Must not perform OCR work at import time.
- Must return OCR Result for expected failures instead of throwing uncaught
  exceptions.
- Must not depend on cascade controller behavior.

## OCR Request

Represents one image OCR attempt.

**Fields**
- `image_path`: optional local image path.
- `image_bytes`: optional image bytes.
- `language_hints`: list of requested language hints, default Arabic and English.
- `mode`: `normal` or `high_accuracy`.
- `preprocessing_variant`: optional placeholder for later image-processing
  phases.
- `allow_online`: boolean.
- `allow_offline`: boolean.
- `timeout_seconds`: positive number for engine calls.

**Validation Rules**
- Exactly one of `image_path` or `image_bytes` must be provided.
- Language hints must include only supported values for Phase 1.
- Timeout must be positive.
- Online engine requires `allow_online`.
- Local engines require `allow_offline`.

## OCR Result

Structured outcome from one OCR engine.

**Fields**
- `engine_name`: stable engine identifier.
- `raw_text`: OCR text, empty when unavailable.
- `clean_text`: optional placeholder, normally empty in Phase 1.
- `confidence`: optional provider or engine confidence.
- `quality_score`: optional placeholder for later quality logic.
- `duration_ms`: non-negative duration.
- `success`: boolean.
- `error_code`: optional stable failure code.
- `error_message`: optional human-readable message.
- `fallback_used`: boolean, always false in Phase 1 independent engine tests.
- `metadata`: safe metadata for default logs.

**Validation Rules**
- Success requires non-empty, non-weak raw text.
- Empty output returns `NO_TEXT_DETECTED`.
- Weak output returns `WEAK_OCR_RESULT`.
- Failure requires `error_code` and `error_message`.
- Default metadata must not contain raw OCR text.

## OCR Engine Error

Stable failure classification for engine outcomes.

**Values**
- `OCR_MISSING_CREDENTIAL`
- `OCR_PROVIDER_TIMEOUT`
- `OCR_PROVIDER_ERROR`
- `OCR_MALFORMED_RESPONSE`
- `OCR_IMAGE_NOT_FOUND`
- `OCR_MODEL_LOAD_ERROR`
- `OCR_EXECUTABLE_NOT_FOUND`
- `OCR_LANGUAGE_DATA_MISSING`
- `NO_TEXT_DETECTED`
- `WEAK_OCR_RESULT`
- `OCR_UNEXPECTED_ERROR`

**Validation Rules**
- Error codes must be stable enough for later spoken-message mapping.
- Expected environment failures must use explicit codes instead of generic
  unexpected errors.

## Sample Image Fixture

Small local input used for deterministic tests.

**Fields**
- `fixture_id`: stable name.
- `language_case`: `arabic`, `english`, `mixed`, or `no_text`.
- `path`: local fixture path.
- `expected_text_note`: short expectation or assertion note.

**Validation Rules**
- Fixtures must be small and safe to store in the repository.
- Fixtures must not be captured from sensitive user content.
- Camera hardware is not required to create or use fixtures.

## State Transitions

```text
Request created
  -> Engine availability checked
  -> Engine recognizes image
  -> Result returned as success, no-text, weak-result, or failure

Project imported
  -> Local accuracy engine object may be constructed
  -> Heavy model remains unloaded
  -> First local OCR request triggers model load
```
