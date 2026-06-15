# Known OCR Failure Cases

## kf-001: path_timeout

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-002: unexpected_benchmark_failure

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-003: path_timeout

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-004: unexpected_benchmark_failure

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-005: path_timeout

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-006: unexpected_benchmark_failure

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-007: path_timeout

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-008: unexpected_benchmark_failure

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-009: path_timeout

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-010: unexpected_benchmark_failure

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-011: path_timeout

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-012: unexpected_benchmark_failure

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-013: path_timeout

- Sample: english_angled_001
- Scenarios: angled_image, printed_document
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-014: unexpected_benchmark_failure

- Sample: english_angled_001
- Scenarios: angled_image, printed_document
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-015: path_timeout

- Sample: mixed_far_receipt_001
- Scenarios: far_image, receipt
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-016: unexpected_benchmark_failure

- Sample: mixed_far_receipt_001
- Scenarios: far_image, receipt
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-017: path_timeout

- Sample: english_blurry_sign_001
- Scenarios: blurry_image, sign
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-018: unexpected_benchmark_failure

- Sample: english_blurry_sign_001
- Scenarios: blurry_image, sign
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-019: path_timeout

- Sample: arabic_blurry_package_001
- Scenarios: blurry_image, medicine_package
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-020: unexpected_benchmark_failure

- Sample: arabic_blurry_package_001
- Scenarios: blurry_image, medicine_package
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-021: path_timeout

- Sample: english_far_document_001
- Scenarios: far_image, printed_document
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-022: unexpected_benchmark_failure

- Sample: english_far_document_001
- Scenarios: far_image, printed_document
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-023: path_timeout

- Sample: mixed_low_light_sign_001
- Scenarios: low_light, sign
- Likely cause: OCR path timeout
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.

## kf-024: unexpected_benchmark_failure

- Sample: mixed_low_light_sign_001
- Scenarios: low_light, sign
- Likely cause: unknown
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Inspect safe benchmark metadata and rerun the controlled fixture.
