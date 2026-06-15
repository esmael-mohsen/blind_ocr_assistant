# Known OCR Failure Cases

## kf-001: weak_ocr_result

- Sample: english_document_normal_001
- Scenarios: normal_quality, printed_document
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.
