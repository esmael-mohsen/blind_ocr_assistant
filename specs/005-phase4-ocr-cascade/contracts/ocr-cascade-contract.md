# Contract: OCR Quality and Cascade Routing

## Scope

This contract defines the Phase 4 internal Python interfaces for OCR quality
scoring and cascade routing. It is not an HTTP API and does not perform camera
capture, best-frame selection, text cleanup, voice command handling, TTS,
translation, or full assistant orchestration.

## OCR Quality Contract

```text
assess_ocr_quality(text, language_hints=None, threshold=0.70) -> OCRQualityReport
```

**Required behavior**

- Empty text is not acceptable.
- Very short text is weak unless it clearly passes configured quality rules.
- Symbol-heavy text is weak.
- Excessive spacing and repeated characters reduce score.
- Severe Arabic fragmentation reduces score.
- Valid Arabic, English, and mixed Arabic-English text can be acceptable.
- Scores of 0.70 or higher are acceptable.
- Scores below 0.70 are weak.

## Cascade Request Contract

```text
OCRCascadeRequest
- image
- language_hints
- allow_online
- allow_offline
- high_accuracy
- image_ready_for_ocr
- quality_threshold
- max_attempts_per_engine
- sensitive_text_logging_enabled
```

**Required behavior**

- If `image_ready_for_ocr` is false, return `IMAGE_NOT_READY_FOR_OCR` without
  calling OCR engines.
- If online OCR is unavailable, disabled, or disallowed, skip online OCR.
- Each allowed engine is attempted at most once per cascade request by default.
- Online availability check timeout is treated as unavailable for the current
  request.

## Normal Cascade Contract

```text
run_ocr_cascade(request, engines, online_status_provider) -> OCRCascadeResult
```

**Required behavior**

- Online mode order is online primary, local accuracy fallback, emergency
  fallback.
- Offline mode order is local accuracy fallback, emergency fallback.
- A good online primary result is accepted without fallback.
- Weak or failed online primary result triggers local accuracy fallback.
- Weak or failed local accuracy result triggers emergency fallback.
- All-engine failure returns `ALL_OCR_ENGINES_FAILED` or the most specific
  stable failure available.

## High Accuracy Contract

**Required behavior**

- When high accuracy is requested and online OCR is allowed, compare online
  primary and local accuracy results before selecting.
- Select the higher-quality acceptable result.
- If acceptable scores differ by less than 0.05, prefer local accuracy OCR.
- If scores remain tied after that, use shorter duration as the final
  tie-breaker.
- Attempt emergency OCR only when compared primary candidates fail or are weak.

## Result Contract

```text
OCRCascadeResult
- success
- selected_engine
- selected_result
- attempts
- fallback_used
- offline_route_used
- high_accuracy_used
- quality_report
- duration_ms
- error
- guidance
- safe_metadata
```

**Required behavior**

- Attempt path is ordered and deterministic.
- Selected result must have quality score at or above the threshold.
- Failure result must include a stable error code and guidance.
- Safe metadata may include engine names, durations, quality scores, fallback
  status, and failure codes.

## Privacy and Logging Contract

Default logs may include:

- attempted engine path
- selected engine
- duration summary
- quality score
- fallback-used status
- offline route status
- high-accuracy status
- failure code

Default logs must not include:

- raw OCR text
- clean text
- image contents
- uploaded payloads
- secrets
- permanent debug paths

OCR text may be logged only when both debug mode and explicit sensitive-text
logging are enabled.

## Phase Boundary Contract

Phase 4 must not call camera capture, best-frame selection, text cleanup,
translation, TTS, voice command recognition, or full assistant workflow
controllers. It returns structured OCR output and safe metadata for later phases.
