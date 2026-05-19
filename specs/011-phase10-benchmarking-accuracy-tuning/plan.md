# Implementation Plan: Phase 10 Benchmarking and Accuracy Tuning

**Branch**: `011-phase10-benchmarking-accuracy-tuning` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-phase10-benchmarking-accuracy-tuning/spec.md`

## Summary

Phase 10 adds a repeatable local OCR benchmark workflow for Arabic, English,
mixed text, and difficult real-world capture scenarios. The implementation will
create safe benchmark fixtures, expected-text references, benchmark data
models, a one-command benchmark runner, privacy-safe timestamped result output,
engine/path comparison, evidence-based tuning recommendations, and methodology
documentation. This phase measures and recommends tuning for existing image
quality, OCR quality, preprocessing, cascade, and frame-selection behavior; it
does not add new OCR engines, paid services, cloud storage, user accounts,
visual UI, deployment services, or normal assistant command categories.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-9 modules; standard library
dataclasses, enums, JSON/CSV file handling, path handling, timestamps, and
statistics; existing OpenCV/numpy image fixture handling where available;
existing OCR engine wrappers, OCR cascade, OCR quality scorer, image quality
checker, preprocessing variants, and frame selector. No new mandatory paid or
cloud dependency is required.

**Storage**: Local filesystem only. Benchmark samples live under
`tests/benchmark/` or controlled fixture paths. Benchmark result sets are
written to timestamped directories under `benchmark_results/` and are not
overwritten by default. Default summaries and logs exclude private image
payloads, raw OCR text, clean text, translated text, secrets, and debug artifact
paths.

**Testing**: Unit tests for benchmark dataset validation, expected-text
normalization, safe metadata, result serialization, result timestamping,
engine-unavailable handling, tuning recommendation gates, and scope boundaries.
Integration tests use mocked OCR/image-quality/frame-selection boundaries to
validate full benchmark runs and comparison summaries without live OCR or
hardware. Optional live benchmark runs remain manual.

**Target Platform**: Development on Windows/Linux with mocked or local fixture
inputs; primary target remains Raspberry Pi OS or Ubuntu-based Linux on
Raspberry Pi 4 Model B with optional Orbbec Astra Pro sample collection.

**Project Type**: Single local Python assistive application with an importable
benchmark module and CLI script.

**Performance Goals**: Benchmark runs should complete deterministically for
the minimum controlled 12-sample fixture set using mocked engines in seconds.
Live OCR benchmark duration is allowed to vary by engine/network, but each
sample/path result must record duration and structured unavailable/failure
outcomes. Benchmark execution must be bounded by configured OCR timeouts and
must not run continuous video OCR.

**Constraints**: No paid services; no mandatory cloud dependency; no user
accounts; no cloud storage; no new OCR engines; no full parallel OCR execution
by default; do not modify normal read/translate workflows from benchmark code;
one benchmark run writes one timestamped local result set; default logs and
summaries remain privacy-safe; tuning recommendations are evidence only unless
later tasks explicitly apply safe threshold changes.

**Scale/Scope**: Minimum controlled dataset is 12 safe local samples with
overlapping labels allowed, covering Arabic, English, mixed text, book page,
printed document, medicine package, receipt, sign, low light, angle, far image,
and blurry image scenarios. Expected-text references are required for all
normal-quality language samples and at least 50 percent of difficult scenario
samples.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. The benchmark produces accessible pass/fail
  summaries and methodology without requiring visual inspection of image
  previews.
- Accuracy Before Speed: PASS. The feature exists to measure OCR quality,
  rejected-image behavior, fallback outcomes, and threshold changes before
  accepting tuning.
- Free Online-First, Offline-Fallback: PASS. Existing free OCR paths may be
  measured, but unavailable online OCR is recorded as an optional-path outcome
  and does not block local benchmark runs.
- Graceful Degradation: PASS. Engine-unavailable, online-unavailable, rejected
  image, no-text, weak OCR, timeout, and unexpected benchmark failures become
  structured result records.
- Privacy by Default: PASS. Benchmark outputs contain safe metadata by default;
  private text and image payloads are excluded unless explicit safe fixtures or
  debug settings allow them.
- Modular Engines: PASS. Benchmark orchestration calls existing OCR, image
  quality, cascade, and frame-selection boundaries instead of coupling to
  provider internals.
- Testability and Observability: PASS. The plan requires deterministic unit and
  mocked integration tests plus result fields for scenario, language, engine,
  duration, quality score, fallback, and failure reason.
- Raspberry Pi Resource Awareness: PASS. Runs are local, bounded by configured
  timeouts, sequential by default, and do not add continuous OCR or mandatory
  heavy model loading at import time.

Post-design re-check: PASS. The research, data model, contract, and quickstart
preserve privacy, free-service constraints, modular boundaries, deterministic
validation, and Raspberry Pi resource limits. No complexity exceptions are
required.

## Project Structure

### Documentation (this feature)

```text
specs/011-phase10-benchmarking-accuracy-tuning/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- benchmark-workflow-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
scripts/
`-- benchmark_ocr.py

modules/
|-- benchmark/
|   |-- __init__.py
|   |-- benchmark_models.py
|   |-- dataset_loader.py
|   |-- expected_text.py
|   |-- runner.py
|   |-- result_writer.py
|   `-- tuning.py
|-- camera/
|-- image_processing/
|-- ocr/
`-- common/

tests/
|-- benchmark/
|   |-- README.md
|   |-- manifest.json
|   |-- expected/
|   `-- samples/
|-- unit/
|   |-- test_benchmark_models.py
|   |-- test_benchmark_dataset_loader.py
|   |-- test_benchmark_expected_text.py
|   |-- test_benchmark_runner.py
|   |-- test_benchmark_result_writer.py
|   |-- test_benchmark_tuning.py
|   |-- test_benchmark_logging_privacy.py
|   `-- test_benchmark_scope_boundaries.py
`-- integration/
    `-- test_benchmark_workflow.py

benchmark_results/
`-- <timestamped-run-id>/
    |-- results.json
    |-- summary.json
    `-- known_failures.md

docs/
`-- benchmark_methodology.md
```

**Structure Decision**: Add a focused `modules.benchmark` package because Phase
10 needs reusable benchmark models, loading, comparison, result writing, and
tuning analysis without mixing benchmark-only behavior into the user-facing
assistant workflow. Keep `scripts/benchmark_ocr.py` as a thin CLI wrapper.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 10.
