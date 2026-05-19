# Phase 10 Benchmark Methodology

## Dataset Policy

The controlled benchmark dataset lives under `tests/benchmark/` and is defined
by `manifest.json`. It must contain at least 12 safe local samples with labels
covering Arabic, English, mixed text, book page, printed document, medicine
package, receipt, sign, low light, angled image, far image, and blurry image.
One sample may carry multiple labels.

Manual private samples must stay outside version control. Local manifests may
reference them only with `manual_private` or `debug_only` classification.

## Expected-Text Policy

Expected text is required for all normal-quality Arabic, English, and mixed
samples. It is also required for at least half of difficult samples. Expected
text fixtures must be sanitized and safe to commit.

## Normalization Policy

Expected-text comparison collapses repeated whitespace and line breaks. It
preserves Arabic characters, English letters, numbers, prices, and meaningful
punctuation so receipts, labels, and mixed-language text remain measurable.

## Result Fields

Each result records the sample ID, OCR path, language label, scenario labels,
success status, duration, text length, OCR quality score when available,
expected-match score when available, fallback marker, failure category, and
privacy-safe metadata. It does not store raw OCR text.

## Privacy Behavior

Default benchmark outputs exclude image payloads, raw OCR text, clean text,
translated text, provider secrets, endpoint credentials, and private debug
paths. `results.json`, `summary.json`, `known_failures.md`, and documentation
examples are designed to be shareable as safe development evidence.

## Best-Path Interpretation

Best-path summaries are scenario-level hints, not automatic routing changes.
Selection prefers expected-match score, then quality score, then success, then
shorter duration. Maintainers should compare repeated timestamped runs before
changing runtime behavior.

## Tuning Gates

Tuning recommendations are evidence only. They remain unaccepted unless the
evidence is measured, tradeoffs are documented, and normal Arabic, English, and
mixed samples do not regress. Phase 10 does not automatically rewrite image
quality, OCR quality, preprocessing, or frame-selection thresholds.

## Known Failure Interpretation

Known failure reports group rejected images, weak OCR, no-text results, engine
unavailable cases, path timeouts, and unexpected benchmark failures. Each case
names the sample ID, affected scenarios, likely cause, user impact, and a safe
follow-up. Known failure reporting distinguishes capture-quality problems from
OCR routing and engine availability problems when the result category allows it.
