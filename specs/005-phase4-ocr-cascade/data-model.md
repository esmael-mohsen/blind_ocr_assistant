# Data Model: Phase 4 OCR Cascade Controller

## OCRCascadeRequest

Represents one OCR cascade decision request for a selected image.

**Fields**

- `image`: Selected image payload or reference from previous phases.
- `language_hints`: Arabic, English, or mixed language hints.
- `allow_online`: Whether online OCR is allowed for this request.
- `allow_offline`: Whether local OCR engines are allowed.
- `high_accuracy`: Whether to compare stronger candidates before acceptance.
- `image_ready_for_ocr`: Whether prior image quality checks accepted the image.
- `quality_threshold`: Acceptance threshold, default 0.70.
- `max_attempts_per_engine`: Default 1.
- `sensitive_text_logging_enabled`: Explicit debug-only text logging flag.

**Validation**

- Image must be present only when `image_ready_for_ocr` is true.
- If `image_ready_for_ocr` is false, the cascade returns
  `IMAGE_NOT_READY_FOR_OCR` and does not run OCR engines.
- At least one of `allow_online` or `allow_offline` must be true.
- Quality threshold defaults to 0.70.

## OCRAttempt

Represents one attempted or skipped OCR engine path.

**Fields**

- `engine_name`: Online primary, local accuracy, or emergency OCR engine.
- `attempt_order`: Ordered position in the cascade.
- `status`: `skipped`, `success`, `weak`, `failed`, or `timeout`.
- `duration_ms`: Attempt duration when attempted.
- `ocr_result`: Structured OCR result when available.
- `quality_report`: OCR quality report when text was produced.
- `error_code`: Stable failure code when attempt fails or is skipped.
- `safe_metadata`: Metadata safe for logs and result summaries.

**Validation**

- Attempt order is deterministic.
- Each engine appears at most once by default.
- Raw OCR text is excluded from safe metadata by default.

## OCRQualityReport

Describes whether OCR text is good enough to accept.

**Fields**

- `is_acceptable`: Whether the result meets the acceptance threshold.
- `quality_score`: Deterministic score from 0.0 to 1.0.
- `threshold`: Acceptance threshold, default 0.70.
- `issues`: Empty text, short text, symbol noise, excessive spacing, repeated
  characters, Arabic fragmentation, or other stable issue categories.
- `language_mix_status`: Arabic, English, mixed, or unknown.
- `guidance`: Short message suitable for later spoken feedback.

**Validation**

- Scores below 0.70 are weak by default.
- Empty text and no-text cases are never acceptable.
- Valid mixed Arabic-English text must not be rejected only because it is mixed.

## OCRCascadeResult

Represents the final cascade outcome.

**Fields**

- `success`: Whether an acceptable OCR result was selected.
- `selected_engine`: Engine name for the accepted result.
- `selected_result`: Accepted OCR result when successful.
- `attempts`: Ordered list of OCR attempts and skips.
- `fallback_used`: Whether any fallback engine was attempted.
- `offline_route_used`: Whether online OCR was skipped for offline routing.
- `high_accuracy_used`: Whether comparison mode was used.
- `quality_report`: Quality report for the selected result or final weak result.
- `duration_ms`: Total cascade duration.
- `error`: Optional cascade error.
- `guidance`: Short guidance suitable for later spoken feedback.
- `safe_metadata`: Metadata safe for default logs.

**Validation**

- Success requires a selected result with quality score at or above 0.70.
- Failure requires a stable error and actionable guidance.
- Attempt path remains deterministic for the same inputs and mocked outcomes.

## OCRCascadeError

Stable failure classification for cascade decisions.

**Codes**

- `IMAGE_NOT_READY_FOR_OCR`
- `ONLINE_OCR_UNAVAILABLE`
- `ONLINE_OCR_TIMEOUT`
- `WEAK_OCR_RESULT`
- `LOCAL_OCR_UNAVAILABLE`
- `EMERGENCY_OCR_UNAVAILABLE`
- `NO_TEXT_DETECTED`
- `ALL_OCR_ENGINES_FAILED`
- `OCR_CASCADE_UNEXPECTED_ERROR`

**Rules**

- Expected failures return human-readable guidance.
- Errors must not expose raw OCR text, image contents, secrets, or debug paths.

## State Transitions

```text
request_received
  -> image_readiness_check
  -> online_availability_check | offline_route
  -> online_primary_attempt | local_accuracy_attempt
  -> accept_result | fallback_to_local | fallback_to_emergency
  -> high_accuracy_compare | final_failure
  -> completed
```

Image-not-ready requests transition directly from `image_readiness_check` to
`final_failure` without running OCR engines.
