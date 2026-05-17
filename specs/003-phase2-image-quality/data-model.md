# Data Model: Phase 2 Image Processing and Quality Checking

## Image Input

Represents one still image submitted for quality assessment and optional
preprocessing.

**Fields**
- `image_path`: optional local image path.
- `image_bytes`: optional encoded image bytes.
- `image_array`: optional in-memory image array.
- `source_id`: optional non-sensitive identifier for logs and tests.

**Validation Rules**
- Exactly one image source must be provided.
- Input must decode into a valid still image with positive width and height.
- Missing, empty, unreadable, or unsupported input returns a structured image
  processing error.
- Camera capture is out of scope; future camera frames may be adapted into this
  same input shape.

## Image Quality Report

Structured outcome from one quality assessment.

**Fields**
- `is_acceptable`: boolean decision for the normal OCR path.
- `overall_status`: `acceptable`, `rejected`, or `uncertain`.
- `quality_score`: normalized overall score.
- `brightness_status`: named lighting category.
- `blur_status`: named sharpness category.
- `contrast_status`: named contrast category.
- `text_presence_status`: named text-presence category.
- `guidance`: bilingual guidance message.
- `primary_issue`: main reason for rejection or uncertainty.
- `metadata`: safe metadata for default logs.

**Validation Rules**
- Clearly poor or uncertain images must set `is_acceptable=false`.
- Accepted reports must include every individual quality status.
- Rejected and uncertain reports must include one primary issue and actionable
  bilingual guidance.
- Metadata must not contain image contents, extracted text, or filesystem debug
  artifact paths unless debug mode explicitly allows them later.

## Quality Finding

Classified result for one quality dimension.

**Fields**
- `dimension`: `brightness`, `blur`, `contrast`, or `text_presence`.
- `status`: stable named category for the dimension.
- `score`: normalized score for observability and tuning.
- `message_key`: stable key used to choose guidance.

**Validation Rules**
- Status names are stable and testable even if numeric thresholds change.
- Scores must be bounded and comparable within the same dimension.
- A failing finding can become the report's `primary_issue`.

## Guidance Message

Short user-facing correction text suitable for later speech.

**Fields**
- `category`: `ready`, `improve_lighting`, `hold_steady`, `increase_contrast`,
  `point_to_text`, `recapture`, or `invalid_image`.
- `english_text`: spoken-ready English guidance.
- `arabic_text`: spoken-ready Arabic guidance.

**Validation Rules**
- English and Arabic text must both be present.
- Guidance must be actionable without visual-only instructions.
- Guidance must be short enough for later TTS use.

## Preprocessing Variant Set

Named image outputs prepared for later OCR paths.

**Fields**
- `source_id`: copied from Image Input when available.
- `original_preserved`: boolean confirming the source image was not mutated.
- `variants`: map of variant name to image data or structured variant failure.
- `metadata`: safe metadata with variant names and dimensions.

**Required Variant Names**
- `online_light`: light enhancement for later online OCR.
- `local_natural`: minimal or natural enhancement for later local accuracy OCR.
- `emergency_strong`: stronger high-contrast preparation for later emergency
  OCR.

**Validation Rules**
- Preprocessing runs in the normal workflow only after an accepted quality
  report.
- The original input must not be mutated.
- One variant failure must not prevent reporting the status of other variants.
- Variant metadata must not include image contents.

## Quality Thresholds

Configurable limits used to classify image quality.

**Fields**
- `min_brightness`
- `max_brightness`
- `min_sharpness`
- `min_contrast`
- `min_text_presence`
- `min_overall_score`

**Validation Rules**
- Thresholds must be bounded and internally consistent.
- Tests validate named categories and decisions rather than exact default
  numbers.
- Defaults must be conservative and suitable for later tuning.

## Image Processing Error

Stable failure classification for expected Phase 2 failures.

**Values**
- `IMAGE_INPUT_MISSING`
- `IMAGE_INPUT_UNREADABLE`
- `IMAGE_UNSUPPORTED_FORMAT`
- `IMAGE_INVALID_DATA`
- `IMAGE_TOO_DARK`
- `IMAGE_TOO_BRIGHT`
- `IMAGE_TOO_BLURRY`
- `IMAGE_LOW_CONTRAST`
- `IMAGE_TEXT_NOT_FOUND`
- `IMAGE_QUALITY_UNCERTAIN`
- `IMAGE_PREPROCESSING_FAILED`
- `IMAGE_UNEXPECTED_ERROR`

**Validation Rules**
- Expected failures must return structured results instead of uncaught
  exceptions.
- Error values must be stable enough for later spoken-message mapping.

## State Transitions

```text
Image input received
  -> Input decoded and validated
  -> Individual quality findings produced
  -> Overall quality report produced
  -> If acceptable: preprocessing may produce named variants
  -> If rejected or uncertain: corrective guidance returned; no automatic preprocessing

Quality thresholds configured
  -> Thresholds validated
  -> Image quality decisions use named categories
  -> Tests assert categories and decisions, not exact default numbers
```
