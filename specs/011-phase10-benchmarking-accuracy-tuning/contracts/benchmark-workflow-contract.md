# Contract: Phase 10 Benchmark Workflow

## Purpose

Define the maintainer-facing benchmark workflow contract for Phase 10. The
contract describes inputs, outputs, privacy guarantees, failure behavior, and
acceptance expectations for the local OCR benchmark runner and related tuning
analysis.

## Command Contract

### Command

```powershell
python scripts/benchmark_ocr.py --dataset tests/benchmark/manifest.json
```

Optional flags may be added during implementation, but must preserve these
contract behaviors:

- `--dataset PATH`: local manifest path.
- `--output-dir PATH`: local benchmark results root, default
  `benchmark_results/`.
- `--paths VALUE`: requested OCR paths or comparison mode.
- `--offline`: skip online OCR paths and record them as disabled when relevant.
- `--debug-text`: explicitly allow safe fixture OCR text in detailed debug
  artifacts only; disabled by default.

Implemented command behavior:

- `--paths cascade` measures the cascade path only.
- `--paths compare` expands to `ocr_space`, `paddleocr`, `tesseract`, and
  `cascade`.
- `--paths` also accepts comma-separated path names and aliases such as
  `online`, `local`, `paddle`, and `emergency`.
- Missing live path adapters are recorded as `online_unavailable` or
  `engine_unavailable`; the CLI smoke run does not start the live assistant.

## Dataset Manifest Contract

The benchmark manifest must describe a local dataset with this shape:

```json
{
  "dataset_id": "phase10-controlled",
  "samples": [
    {
      "sample_id": "arabic_book_normal_001",
      "image_path": "tests/benchmark/samples/arabic_book_normal_001.png",
      "scenario_labels": ["book_page", "normal_quality"],
      "language_label": "ar",
      "quality_label": "normal",
      "expected_text_id": "arabic_book_normal_001",
      "privacy_classification": "safe_fixture"
    }
  ],
  "expected_texts": [
    {
      "expected_text_id": "arabic_book_normal_001",
      "text_path": "tests/benchmark/expected/arabic_book_normal_001.txt",
      "language_label": "ar",
      "normalization_policy": "preserve_meaning",
      "privacy_classification": "safe_fixture"
    }
  ]
}
```

### Manifest Rules

- At least 12 samples are required.
- Labels must cover Arabic, English, mixed text, book page, printed document,
  medicine package, receipt, sign, low light, angled image, far image, and
  blurry image.
- Expected text is required for all normal-quality language samples and at
  least 50 percent of difficult scenario samples.
- Paths must be local project-relative paths.
- Private text and private image paths must not be written to default summaries.

## Result Output Contract

Each run creates a new timestamped directory:

```text
benchmark_results/<run-id>/
|-- results.json
|-- summary.json
`-- known_failures.md
```

Existing run directories must not be overwritten by default.

### `results.json`

```json
{
  "run_id": "20260518-214500-phase10",
  "dataset_id": "phase10-controlled",
  "status": "success",
  "results": [
    {
      "sample_id": "arabic_book_normal_001",
      "ocr_path": "ocr_space",
      "scenario_labels": ["book_page", "normal_quality"],
      "language_label": "ar",
      "success": true,
      "duration_ms": 1200,
      "text_length": 245,
      "quality_score": 0.84,
      "expected_match_score": 0.78,
      "fallback_used": false,
      "failure_category": null,
      "safe_metadata": {
        "engine_name": "ocr_space",
        "sample_id": "arabic_book_normal_001"
      }
    }
  ]
}
```

### `summary.json`

```json
{
  "run_id": "20260518-214500-phase10",
  "dataset_id": "phase10-controlled",
  "sample_count": 12,
  "result_count": 36,
  "status_counts": {
    "success": 24,
    "failed": 8,
    "unavailable": 4
  },
  "best_paths_by_scenario": {
    "book_page": "ocr_space",
    "receipt": "paddleocr"
  },
  "tuning_recommendations": [],
  "privacy": {
    "contains_raw_text": false,
    "contains_image_payloads": false,
    "contains_secrets": false
  }
}
```

## Expected Text Comparison Contract

Comparison must:

- Normalize repeated whitespace and line-break differences.
- Preserve Arabic characters, English letters, numbers, prices, and meaningful
  punctuation.
- Produce a score between `0.0` and `1.0`.
- Return structured unavailable comparison when expected text is missing.

## Failure Contract

The benchmark workflow must return structured outcomes for:

- dataset missing
- manifest invalid
- sample missing
- expected text missing when required
- unsupported image file
- image rejected by quality checks
- online OCR disabled or unavailable
- local OCR unavailable
- OCR timeout
- weak OCR result
- no text detected
- unexpected benchmark failure
- interrupted benchmark run

Failures must not expose raw OCR text, clean text, image bytes, provider
secrets, endpoint credentials, or private debug paths in default outputs.

Implemented failure categories are:

- `dataset_missing`
- `manifest_invalid`
- `sample_missing`
- `expected_text_missing`
- `unsupported_image_file`
- `image_rejected`
- `online_disabled`
- `online_unavailable`
- `local_unavailable`
- `path_timeout`
- `weak_ocr_result`
- `no_text_detected`
- `engine_unavailable`
- `unexpected_benchmark_failure`
- `interrupted_benchmark_run`

## Tuning Recommendation Contract

Each recommendation must include:

- target area
- current value when applicable
- proposed value when applicable
- affected scenarios
- measured evidence summary
- expected benefit
- regression risk
- accepted state, default `false`

Recommendations must not be accepted when evidence is missing, tradeoffs are
unresolved, or normal Arabic, English, or mixed samples regress.

## Scope Boundary Contract

Phase 10 benchmark code must not:

- add OCR engines
- add translation engines
- add STT or TTS engines
- add assistant command categories
- start the live assistant loop
- require cloud storage
- create user accounts
- require paid services
- overwrite prior benchmark result sets by default
