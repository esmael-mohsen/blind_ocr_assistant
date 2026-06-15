# Known OCR Failure Cases

## kf-001: image_rejected

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: capture quality
- User impact: The assistant would ask the user to recapture before reading.
- Recommended follow-up: Review image quality thresholds and capture guidance.

## kf-002: weak_ocr_result

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-003: no_text_detected

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review text-region detection and OCR path routing.

## kf-004: engine_unavailable

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: local OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm offline OCR dependency installation guidance.

## kf-005: path_timeout

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-006: unexpected_benchmark_failure

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.
