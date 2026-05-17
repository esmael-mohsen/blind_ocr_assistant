# Architecture

Phase 0 creates an importable scaffold for the future assistive OCR workflow.

## Phase 0 Boundary

Implemented behavior is limited to:

- command help
- bootstrap self-check
- safe configuration defaults
- local operational logging
- common success/failure results
- importable package placeholders

Reserved package areas are present for future phases:

- `modules.camera`
- `modules.image_processing`
- `modules.ocr`
- `modules.text`
- `modules.translation`
- `modules.voice`
- `modules.assistant`

These packages must remain behavior-free in Phase 0. OCR, camera capture,
voice recognition, text-to-speech, translation, and full assistive workflow logic
begin in later phases.

## Phase 1 OCR Engine Layer

Phase 1 implements independent OCR engines behind `modules.ocr.OCRBaseEngine`.
The layer owns:

- `OCRRequest`
- `OCRResult`
- stable OCR error codes
- online OCR engine wrapper
- local accuracy OCR wrapper with lazy loading
- emergency OCR wrapper

Phase 1 still does not implement camera capture, image-quality pre-checking,
best-frame selection, OCR cascade routing, text cleanup, voice commands, TTS, or
translation.

Default OCR logs must contain metadata only: engine name, duration, success
status, and error code. Raw OCR text is excluded unless an explicit debug text
logging path is added later.

## Phase 2 Image Processing Layer

Phase 2 implements local still-image quality checks and preprocessing in
`modules.image_processing`. The layer owns:

- `ImageInput`
- `ImageQualityReport`
- image quality statuses and stable image-processing error codes
- bilingual guidance messages for later spoken feedback
- text-presence estimation without OCR
- `online_light`, `local_natural`, and `emergency_strong` preprocessing variants

Poor or uncertain images are blocked from the normal OCR path with corrective
guidance. Rejected images do not automatically enter preprocessing. Accepted
images may produce the three named OCR-preparation variants while preserving the
original image.

Phase 2 still does not implement camera capture, depth analysis, best-frame
selection, OCR engine execution, OCR cascade routing, text cleanup, voice
commands, TTS playback, or translation.

Default image-processing logs must contain metadata only: statuses, scores,
guidance category, dimensions, variant names, and error codes. Image bytes,
image arrays, OCR text, private document content, and debug artifact paths are
excluded by default.
