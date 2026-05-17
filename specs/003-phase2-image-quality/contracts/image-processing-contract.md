# Image Processing Contract: Phase 2

## Purpose

Define the public module contract for local image quality checks, text-presence
estimation, bilingual guidance, and preprocessing variants before camera capture
or OCR cascade routing exists.

## Quality Assessment Contract

The image quality layer exposes:

```text
assess_image_quality(input: ImageInput, thresholds: QualityThresholds) -> ImageQualityReport
```

The report must include:

```text
is_acceptable: bool
overall_status: acceptable | rejected | uncertain
quality_score: bounded number
brightness_status: named category
blur_status: named category
contrast_status: named category
text_presence_status: named category
guidance: bilingual GuidanceMessage
primary_issue: optional stable issue code
metadata: dictionary safe for default logs
```

## Text-Region Estimation Contract

The text-region estimator exposes:

```text
estimate_text_presence(input: ImageInput) -> QualityFinding
```

Required text-presence statuses:

```text
likely_text
unlikely_text
uncertain_text
```

The estimator must be deterministic for the same input and must not run OCR.

## Preprocessing Contract

The preprocessing layer exposes:

```text
create_preprocessing_variants(input: ImageInput) -> PreprocessingVariantSet
```

Required variant names:

```text
online_light
local_natural
emergency_strong
```

Rules:

- The original image must not be mutated.
- The normal workflow calls preprocessing only after an accepted quality report.
- Rejected or uncertain images return corrective guidance instead of automatic
  preprocessing.
- A failed variant returns a structured per-variant failure without crashing the
  entire preprocessing call.

## Guidance Contract

Every rejected or uncertain quality report returns one primary guidance category
with both languages:

```text
category: stable guidance category
english_text: short spoken-ready message
arabic_text: short spoken-ready message
```

Guidance must avoid visual-only instructions and must be suitable for later TTS.

## Error Semantics

Expected failures return structured results or exceptions converted to stable
error codes by the caller. Required codes:

```text
IMAGE_INPUT_MISSING
IMAGE_INPUT_UNREADABLE
IMAGE_UNSUPPORTED_FORMAT
IMAGE_INVALID_DATA
IMAGE_TOO_DARK
IMAGE_TOO_BRIGHT
IMAGE_TOO_BLURRY
IMAGE_LOW_CONTRAST
IMAGE_TEXT_NOT_FOUND
IMAGE_QUALITY_UNCERTAIN
IMAGE_PREPROCESSING_FAILED
IMAGE_UNEXPECTED_ERROR
```

## Logging and Privacy Contract

Default metadata may include:

```text
source_id
image_width
image_height
quality_score
status names
guidance category
error code
variant names
duration_ms
```

Default metadata must not include:

```text
raw image bytes
image arrays
OCR text
permanent debug artifact paths
private document content
```

## Out of Scope

This contract does not define camera capture, depth analysis, best-frame
selection, OCR engine execution, OCR cascade routing, text cleanup, voice
commands, TTS playback, or translation.
