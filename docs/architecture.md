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
