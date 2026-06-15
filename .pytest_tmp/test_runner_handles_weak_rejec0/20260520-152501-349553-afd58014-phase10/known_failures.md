# Known OCR Failure Cases

## kf-001: image_rejected

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: capture quality
- User impact: The assistant would ask the user to recapture before reading.
- Recommended follow-up: Review image quality thresholds and capture guidance.

## kf-002: image_rejected

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: capture quality
- User impact: The assistant would ask the user to recapture before reading.
- Recommended follow-up: Review image quality thresholds and capture guidance.

## kf-003: image_rejected

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: capture quality
- User impact: The assistant would ask the user to recapture before reading.
- Recommended follow-up: Review image quality thresholds and capture guidance.

## kf-004: online_disabled

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-005: weak_ocr_result

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-006: weak_ocr_result

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-007: online_disabled

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-008: weak_ocr_result

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-009: weak_ocr_result

- Sample: mixed_receipt_normal_001
- Scenarios: normal_quality, receipt
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-010: online_disabled

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-011: weak_ocr_result

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-012: weak_ocr_result

- Sample: medicine_package_normal_001
- Scenarios: medicine_package, normal_quality
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-013: online_disabled

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-014: weak_ocr_result

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-015: weak_ocr_result

- Sample: street_sign_normal_001
- Scenarios: normal_quality, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-016: online_disabled

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-017: weak_ocr_result

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-018: weak_ocr_result

- Sample: arabic_low_light_001
- Scenarios: book_page, low_light
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-019: online_disabled

- Sample: english_angled_001
- Scenarios: angled_image, printed_document
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-020: weak_ocr_result

- Sample: english_angled_001
- Scenarios: angled_image, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-021: weak_ocr_result

- Sample: english_angled_001
- Scenarios: angled_image, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-022: online_disabled

- Sample: mixed_far_receipt_001
- Scenarios: far_image, receipt
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-023: weak_ocr_result

- Sample: mixed_far_receipt_001
- Scenarios: far_image, receipt
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-024: weak_ocr_result

- Sample: mixed_far_receipt_001
- Scenarios: far_image, receipt
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-025: online_disabled

- Sample: english_blurry_sign_001
- Scenarios: blurry_image, sign
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-026: weak_ocr_result

- Sample: english_blurry_sign_001
- Scenarios: blurry_image, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-027: weak_ocr_result

- Sample: english_blurry_sign_001
- Scenarios: blurry_image, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-028: online_disabled

- Sample: arabic_blurry_package_001
- Scenarios: blurry_image, medicine_package
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-029: weak_ocr_result

- Sample: arabic_blurry_package_001
- Scenarios: blurry_image, medicine_package
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-030: weak_ocr_result

- Sample: arabic_blurry_package_001
- Scenarios: blurry_image, medicine_package
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-031: online_disabled

- Sample: english_far_document_001
- Scenarios: far_image, printed_document
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-032: weak_ocr_result

- Sample: english_far_document_001
- Scenarios: far_image, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-033: weak_ocr_result

- Sample: english_far_document_001
- Scenarios: far_image, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-034: online_disabled

- Sample: mixed_low_light_sign_001
- Scenarios: low_light, sign
- Likely cause: online OCR availability
- User impact: The assistant should continue to the next available OCR path.
- Recommended follow-up: Confirm online OCR configuration remains optional.

## kf-035: weak_ocr_result

- Sample: mixed_low_light_sign_001
- Scenarios: low_light, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.

## kf-036: weak_ocr_result

- Sample: mixed_low_light_sign_001
- Scenarios: low_light, sign
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.
