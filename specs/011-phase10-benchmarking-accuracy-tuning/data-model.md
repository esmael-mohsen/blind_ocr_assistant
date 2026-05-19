# Data Model: Phase 10 Benchmarking and Accuracy Tuning

## BenchmarkDataset

Represents one local benchmark dataset definition.

**Fields**

- `dataset_id`: Stable identifier for the dataset.
- `manifest_path`: Local manifest path.
- `samples`: Ordered list of `BenchmarkSample` entries.
- `minimum_sample_count`: Required minimum, default `12`.
- `created_for_phase`: Phase label, default `phase10`.

**Validation Rules**

- Must contain at least 12 samples.
- Must include labels covering Arabic, English, mixed text, book page, printed
  document, medicine package, receipt, sign, low light, angled image, far
  image, and blurry image.
- A sample may satisfy multiple labels.
- Dataset paths must be local.

**Relationships**

- Has many `BenchmarkSample` entries.
- May be used by many `BenchmarkRun` executions.

## BenchmarkSample

Represents one benchmark image or controlled capture fixture.

**Fields**

- `sample_id`: Unique sample identifier within the dataset.
- `image_path`: Local image or fixture path.
- `scenario_labels`: One or more scenario labels.
- `language_label`: `ar`, `en`, `mixed`, or `unknown`.
- `quality_label`: `normal`, `low_light`, `angled`, `far`, `blurry`, or
  another approved benchmark label.
- `expected_text_id`: Optional link to an `ExpectedTextReference`.
- `privacy_classification`: `safe_fixture`, `manual_private`, or `debug_only`.
- `notes`: Optional safe maintainer notes.

**Validation Rules**

- `sample_id` must be unique within the dataset.
- `image_path` must exist for executable benchmark runs.
- Default logs must not include image bytes or private image paths.
- Safe fixture content may be committed only when intentionally sanitized.
- Normal-quality Arabic, English, and mixed samples must have expected text.

**Relationships**

- May reference one `ExpectedTextReference`.
- Produces one or more `BenchmarkResult` entries per run.

## ExpectedTextReference

Represents safe comparison text for selected benchmark samples.

**Fields**

- `expected_text_id`: Stable reference identifier.
- `text_path`: Local safe fixture text path.
- `language_label`: `ar`, `en`, `mixed`, or `unknown`.
- `normalization_policy`: Policy name, default `preserve_meaning`.
- `privacy_classification`: Must be safe for committed fixtures.

**Validation Rules**

- Expected text must be non-empty.
- Comparison normalizes whitespace and line breaks.
- Comparison preserves Arabic and English language-bearing characters, numbers,
  prices, and meaningful punctuation.
- Private expected text must not be written to default result summaries.

**Relationships**

- May be used by multiple `BenchmarkSample` entries when appropriate.

## BenchmarkRun

Represents one timestamped benchmark execution.

**Fields**

- `run_id`: Timestamped unique identifier.
- `dataset_id`: Dataset used for the run.
- `started_at`: Run start timestamp.
- `completed_at`: Run completion timestamp when available.
- `environment`: Safe environment metadata, such as platform and availability
  of online/local OCR paths.
- `requested_paths`: Ordered list of OCR paths requested for measurement.
- `result_directory`: Timestamped local output directory.
- `status`: `success`, `partial`, `failed`, or `interrupted`.
- `summary`: Aggregate counts and scenario summaries.

**Validation Rules**

- `run_id` must be unique.
- Result directory must not overwrite a previous run by default.
- Interrupted runs must still preserve completed safe result records.
- Environment metadata must exclude secrets and private paths.

**Relationships**

- Belongs to one `BenchmarkDataset`.
- Has many `BenchmarkResult` records.
- May produce many `TuningRecommendation` and `KnownFailureCase` entries.

## BenchmarkResult

Represents one measured result for one sample and one OCR path.

**Fields**

- `run_id`: Parent benchmark run.
- `sample_id`: Sample measured.
- `ocr_path`: Engine or cascade path measured.
- `scenario_labels`: Copied safe labels from the sample.
- `language_label`: Copied language label from the sample.
- `success`: Boolean outcome.
- `duration_ms`: Non-negative duration.
- `text_length`: Length of OCR output when available, never the text itself in
  default summaries.
- `quality_score`: Optional score from existing OCR quality logic.
- `expected_match_score`: Optional comparison score when expected text exists.
- `fallback_used`: Boolean fallback marker where relevant.
- `failure_category`: Optional stable failure category.
- `safe_metadata`: Privacy-safe metadata for logs and summaries.

**Validation Rules**

- Must record either a successful quality outcome or a structured failure.
- Must not include raw OCR text, clean text, translated text, image bytes,
  tokens, secrets, or private debug artifact paths in safe metadata.
- `duration_ms` must be non-negative.
- `quality_score` and `expected_match_score`, when present, must be between
  `0.0` and `1.0`.

**Relationships**

- Belongs to one `BenchmarkRun`.
- Belongs to one `BenchmarkSample`.
- May contribute to `TuningRecommendation`.

## TuningRecommendation

Represents one proposed threshold or scoring adjustment.

**Fields**

- `recommendation_id`: Unique identifier within a run.
- `run_id`: Source benchmark run.
- `target_area`: `image_quality`, `ocr_quality`, `preprocessing`, or
  `frame_selection`.
- `current_value`: Current threshold or score contribution when applicable.
- `proposed_value`: Proposed value when applicable.
- `affected_scenarios`: Scenario labels affected.
- `evidence_summary`: Safe summary of measured evidence.
- `expected_benefit`: Maintainer-readable benefit.
- `regression_risk`: Risk summary.
- `accepted`: Boolean, default `false`.

**Validation Rules**

- Must cite measured evidence.
- Must document affected scenarios and regression risk.
- Must not be accepted if normal Arabic, English, or mixed samples regress.
- Must remain a recommendation unless a later implementation task applies it.

**Relationships**

- Derived from one `BenchmarkRun`.
- References one or more `BenchmarkResult` records by safe identifiers.

## KnownFailureCase

Represents a recurring or important OCR failure found by benchmarking.

**Fields**

- `failure_id`: Unique identifier within a run or methodology document.
- `sample_id`: Related sample when applicable.
- `scenario_labels`: Affected scenario labels.
- `failure_category`: Stable category.
- `likely_cause`: Capture quality, OCR routing, preprocessing, language
  handling, engine limitation, or unknown.
- `user_impact`: Description of assistive reading impact.
- `recommended_follow_up`: Safe next action.

**Validation Rules**

- Must not expose private image content or OCR text in default reports.
- Must distinguish capture-quality problems from OCR-routing problems where
  possible.

**Relationships**

- May reference one or more `BenchmarkResult` records.

## State Transitions

### BenchmarkRun

```text
created -> running -> success
created -> running -> partial
created -> running -> interrupted
created -> failed
```

- `partial` means some samples/paths produced structured failures or were
  unavailable while the run itself completed.
- `interrupted` means the run stopped before all requested work completed but
  completed safe results were written.

### TuningRecommendation

```text
proposed -> accepted
proposed -> rejected
proposed -> deferred
```

- `accepted` requires evidence, documented tradeoffs, and no regression for
  normal Arabic, English, or mixed samples.
