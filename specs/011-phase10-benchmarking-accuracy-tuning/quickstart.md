# Phase 10 Quickstart: Benchmarking and Accuracy Tuning

## Purpose

Phase 10 measures OCR behavior across safe local benchmark samples, compares
existing OCR paths, writes timestamped local result sets, and produces
evidence-based tuning recommendations. It does not start the normal assistant
workflow and does not introduce new OCR engines or paid services.

## Expected Files

```text
modules/benchmark/__init__.py
modules/benchmark/benchmark_models.py
modules/benchmark/dataset_loader.py
modules/benchmark/expected_text.py
modules/benchmark/runner.py
modules/benchmark/result_writer.py
modules/benchmark/tuning.py
scripts/benchmark_ocr.py
tests/benchmark/manifest.json
tests/benchmark/samples/
tests/benchmark/expected/
tests/unit/test_benchmark_models.py
tests/unit/test_benchmark_dataset_loader.py
tests/unit/test_benchmark_expected_text.py
tests/unit/test_benchmark_runner.py
tests/unit/test_benchmark_result_writer.py
tests/unit/test_benchmark_tuning.py
tests/unit/test_benchmark_logging_privacy.py
tests/unit/test_benchmark_scope_boundaries.py
tests/integration/test_benchmark_workflow.py
docs/benchmark_methodology.md
```

## Automated Validation

Run focused Phase 10 tests:

```powershell
python -m pytest tests/unit/test_benchmark_models.py
python -m pytest tests/unit/test_benchmark_dataset_loader.py
python -m pytest tests/unit/test_benchmark_expected_text.py
python -m pytest tests/unit/test_benchmark_runner.py
python -m pytest tests/unit/test_benchmark_result_writer.py
python -m pytest tests/unit/test_benchmark_tuning.py
python -m pytest tests/unit/test_benchmark_logging_privacy.py
python -m pytest tests/unit/test_benchmark_scope_boundaries.py
python -m pytest tests/integration/test_benchmark_workflow.py
```

Or run them together:

```powershell
python -m pytest tests/unit/test_benchmark_models.py tests/unit/test_benchmark_dataset_loader.py tests/unit/test_benchmark_expected_text.py tests/unit/test_benchmark_runner.py tests/unit/test_benchmark_result_writer.py tests/unit/test_benchmark_tuning.py tests/unit/test_benchmark_logging_privacy.py tests/unit/test_benchmark_scope_boundaries.py tests/integration/test_benchmark_workflow.py
```

Run full unit regression:

```powershell
python -m pytest tests/unit
```

Run available quality checks:

```powershell
python -m ruff check .
python -m black --check .
python -m mypy .
```

If optional tools are not installed, record that they could not be run and keep
pytest plus ruff as the required validation baseline.

## Benchmark Smoke Run

After implementation, run the controlled local benchmark:

```powershell
python scripts/benchmark_ocr.py --dataset tests/benchmark/manifest.json
```

Compare all existing OCR paths with online paths disabled:

```powershell
python scripts/benchmark_ocr.py --dataset tests/benchmark/manifest.json --output-dir benchmark_results --paths compare --offline
```

Expected behavior:

- Creates a new timestamped directory under `benchmark_results/`.
- Writes `results.json`, `summary.json`, and `known_failures.md`.
- Records unavailable online or local engines as structured outcomes.
- Excludes raw OCR text, clean text, image payloads, translated text, secrets,
  and private debug paths from default summaries.
- Does not start the live assistant loop, microphone, TTS playback, or
  translation workflow.

Generated artifacts:

- `results.json`: one safe record per sample and requested OCR path.
- `summary.json`: aggregate status, scenario, language, engine, best-path, and
  tuning recommendation summaries.
- `known_failures.md`: grouped safe failure cases and follow-up guidance.

Optional live OCR notes:

- Automated validation uses mocked boundaries or structured unavailable
  outcomes. Live OCR.space, PaddleOCR, and Tesseract adapters can be injected by
  future maintainer scripts without changing the assistant workflow.
- Running `--offline` keeps online OCR disabled and records the disabled online
  path when requested.

## Manual Acceptance

On target hardware or a documented equivalent environment:

1. Add safe manual samples or collect sanitized samples from the target camera.
2. Label samples for Arabic, English, mixed text, and required real-world
   scenarios.
3. Add expected text for all normal-quality language samples and at least half
   of difficult scenario samples.
4. Run the benchmark once with online OCR available when configured.
5. Run the benchmark once with online OCR disabled or unavailable.
6. Confirm each run writes a separate timestamped result set.
7. Confirm methodology documentation identifies best paths and known failures.

Hardware, camera, online OCR, PaddleOCR, and Tesseract availability may vary by
environment. Automated tests must use mocked boundaries where live dependencies
are unavailable.

## Acceptance Checklist

- Dataset contains at least 12 safe local samples.
- Dataset labels cover all required language and scenario categories.
- Expected text exists for required normal and difficult samples.
- Expected-text comparison normalizes harmless whitespace and line breaks.
- Result records include stable scenario, language, duration, score, path, and
  failure fields.
- Engine-unavailable outcomes do not stop unrelated benchmark cases.
- Repeated runs never overwrite prior result sets by default.
- Tuning recommendations cite evidence and document regression risk.
- No accepted recommendation regresses normal Arabic, English, or mixed
  samples.
- Default outputs exclude private text, images, secrets, and debug paths.
- Benchmark code does not add engines, assistant commands, cloud storage,
  user accounts, paid services, or deployment services.
