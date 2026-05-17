# OCR Engine Contract: Phase 1

## Purpose

Define the public module contract for independent OCR engines before cascade
routing exists.

## Engine Interface

Each OCR engine implements:

```text
engine_name -> stable string
is_available() -> bool or availability result
recognize(request: OCRRequest) -> OCRResult
```

## Request Contract

An OCR request must provide exactly one image source:

```text
image_path: optional path
image_bytes: optional bytes
language_hints: list, default ["ar", "en"]
mode: normal | high_accuracy
preprocessing_variant: optional string
allow_online: bool
allow_offline: bool
timeout_seconds: positive number
```

## Result Contract

All engines return:

```text
engine_name: string
raw_text: string
clean_text: optional string
confidence: optional number
quality_score: optional number
duration_ms: non-negative number
success: bool
error_code: optional string
error_message: optional string
fallback_used: bool
metadata: dictionary safe for default logs
```

## Success Semantics

Successful OCR requires meaningful raw text. Empty or weak output is a structured
failure:

```text
NO_TEXT_DETECTED
WEAK_OCR_RESULT
```

## Error Semantics

Expected failures must not crash the program. They return OCR Result with
`success=false`, `error_code`, and `error_message`.

Required stable codes:

```text
OCR_MISSING_CREDENTIAL
OCR_PROVIDER_TIMEOUT
OCR_PROVIDER_ERROR
OCR_MALFORMED_RESPONSE
OCR_IMAGE_NOT_FOUND
OCR_MODEL_LOAD_ERROR
OCR_EXECUTABLE_NOT_FOUND
OCR_LANGUAGE_DATA_MISSING
NO_TEXT_DETECTED
WEAK_OCR_RESULT
OCR_UNEXPECTED_ERROR
```

## Online Engine Rules

- Live online tests are opt-in.
- Missing free credentials skip live tests.
- Transient online failures may retry once.
- Default logs must not include raw OCR text.

## Local Accuracy Engine Rules

- Heavy model loading must be lazy.
- Importing the project or running bootstrap help must not load the model.
- Missing model/package returns `OCR_MODEL_LOAD_ERROR`.

## Emergency Engine Rules

- Missing executable returns `OCR_EXECUTABLE_NOT_FOUND`.
- Missing Arabic or English language data returns `OCR_LANGUAGE_DATA_MISSING`.
- Poor or unreadable input returns `NO_TEXT_DETECTED` or `WEAK_OCR_RESULT`.

## Out of Scope

This contract does not define camera capture, image-quality pre-checking,
best-frame selection, OCR cascade routing, text cleanup, voice commands, TTS, or
translation.
