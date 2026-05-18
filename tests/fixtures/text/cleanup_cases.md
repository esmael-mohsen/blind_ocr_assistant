# Phase 5 Cleanup Fixture Notes

Use these notes to build deterministic tests for text cleanup behavior.

- Preserve raw OCR text exactly in every result.
- Normalize repeated spaces and tabs.
- Collapse single OCR line breaks inside paragraphs.
- Preserve blank-line paragraph breaks.
- Preserve list-like line breaks.
- Normalize Arabic and English punctuation spacing without removing punctuation.
- Preserve uncertain OCR fragments and return warnings instead of deleting them.
- Confirm cleanup is idempotent.

