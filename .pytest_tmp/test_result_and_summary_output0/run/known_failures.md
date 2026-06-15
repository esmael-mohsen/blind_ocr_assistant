# Known OCR Failure Cases

## kf-001: weak_ocr_result

- Sample: arabic_book_normal_001
- Scenarios: book_page, normal_quality
- Likely cause: OCR quality
- User impact: The assistant may avoid reading unreliable or missing text.
- Recommended follow-up: Review preprocessing and OCR quality threshold evidence.
