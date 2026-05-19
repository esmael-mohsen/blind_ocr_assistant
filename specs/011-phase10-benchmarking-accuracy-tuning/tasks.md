# Tasks: Phase 10 Benchmarking and Accuracy Tuning

**Input**: Design documents from `/specs/011-phase10-benchmarking-accuracy-tuning/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/benchmark-workflow-contract.md, quickstart.md

**Tests**: Included because the constitution and feature specification require deterministic validation for benchmark dataset coverage, OCR path comparison, evidence-based tuning recommendations, privacy-safe output, repeated-run retention, and scope boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed earlier phases
- **[Story]**: User story label, such as [US1], [US2], [US3], or [US4]
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 10 benchmark module, script, fixture directories, and test files without changing existing OCR, camera, image-processing, or assistant workflow behavior.

- [X] T001 Create Phase 10 benchmark package placeholders in modules/benchmark/__init__.py, modules/benchmark/benchmark_models.py, modules/benchmark/dataset_loader.py, modules/benchmark/expected_text.py, modules/benchmark/runner.py, modules/benchmark/result_writer.py, and modules/benchmark/tuning.py
- [X] T002 [P] Create benchmark script placeholder in scripts/benchmark_ocr.py
- [X] T003 [P] Create benchmark fixture structure in tests/benchmark/README.md, tests/benchmark/manifest.json, tests/benchmark/samples/.gitkeep, and tests/benchmark/expected/.gitkeep
- [X] T004 [P] Create Phase 10 test placeholders in tests/unit/test_benchmark_models.py, tests/unit/test_benchmark_dataset_loader.py, tests/unit/test_benchmark_expected_text.py, tests/unit/test_benchmark_runner.py, tests/unit/test_benchmark_result_writer.py, tests/unit/test_benchmark_tuning.py, tests/unit/test_benchmark_logging_privacy.py, tests/unit/test_benchmark_scope_boundaries.py, and tests/integration/test_benchmark_workflow.py
- [X] T005 [P] Update .gitignore to keep benchmark_results/ generated run outputs out of version control while preserving benchmark_results/.gitkeep if used
- [X] T006 [P] Add Phase 10 benchmark package exports in modules/benchmark/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define benchmark models, safe metadata behavior, manifest loading, expected-text comparison, timestamped output writing, and CLI argument parsing used by all stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Write failing benchmark model tests for BenchmarkDataset, BenchmarkSample, ExpectedTextReference, BenchmarkRun, BenchmarkResult, TuningRecommendation, KnownFailureCase, enums, validation rules, state transitions, and safe metadata in tests/unit/test_benchmark_models.py
- [X] T008 Implement Phase 10 benchmark data models, enums, validation helpers, and privacy-safe metadata helpers in modules/benchmark/benchmark_models.py
- [X] T009 [P] Write failing expected-text normalization tests for Arabic, English, mixed text, whitespace, line breaks, numbers, prices, punctuation, missing expected text, and match score bounds in tests/unit/test_benchmark_expected_text.py
- [X] T010 Implement expected-text loading, conservative normalization, and expected-match scoring in modules/benchmark/expected_text.py
- [X] T011 [P] Write failing dataset loader tests for manifest shape, local path validation, unique sample IDs, 12-sample minimum, required label coverage, expected-text coverage, and unsupported privacy classifications in tests/unit/test_benchmark_dataset_loader.py
- [X] T012 Implement manifest loading, dataset validation, expected-text linkage, local path resolution, and coverage validation in modules/benchmark/dataset_loader.py
- [X] T013 [P] Write failing result writer tests for timestamped run IDs, non-overwrite behavior, results.json shape, summary.json shape, known_failures.md writing, interrupted-run preservation, and safe path handling in tests/unit/test_benchmark_result_writer.py
- [X] T014 Implement timestamped local result writing, summary writing, known-failure writing, non-overwrite protection, and interrupted-run persistence in modules/benchmark/result_writer.py
- [X] T015 [P] Write failing CLI contract tests for python scripts/benchmark_ocr.py --help, --dataset, --output-dir, --paths, --offline, --debug-text, missing dataset, and no live assistant startup in tests/unit/test_benchmark_runner.py
- [X] T016 Implement CLI argument parsing and thin runner delegation in scripts/benchmark_ocr.py
- [X] T017 Update modules/benchmark/__init__.py to export the implemented models, loader, expected-text, runner, result-writer, and tuning boundaries

**Checkpoint**: Foundation ready. Benchmark models, manifest loading, text comparison, result writing, and CLI contract can be tested without live OCR or hardware.

---

## Phase 3: User Story 1 - Benchmark Real-World OCR Scenarios (Priority: P1) MVP

**Goal**: Provide a repeatable local benchmark dataset and run workflow that records measurable OCR outcomes for Arabic, English, mixed text, and required real-world scenarios.

**Independent Test**: Run the benchmark with mocked OCR boundaries against the controlled manifest and verify every sample produces a result or structured failure with scenario labels, language label, duration, text length, quality score, evaluated path, and privacy-safe metadata.

### Tests for User Story 1

- [X] T018 [P] [US1] Write failing tests for controlled 12-sample manifest coverage, required language labels, required scenario labels, overlapping labels, and expected-text coverage in tests/unit/test_benchmark_dataset_loader.py
- [X] T019 [P] [US1] Write failing tests for benchmark run orchestration over all samples with mocked OCR success, mocked OCR weak output, mocked image rejection, and structured per-sample results in tests/unit/test_benchmark_runner.py
- [X] T020 [P] [US1] Write failing integration test for one full mocked benchmark run from tests/benchmark/manifest.json to timestamped benchmark_results output in tests/integration/test_benchmark_workflow.py
- [X] T021 [P] [US1] Write failing privacy tests proving benchmark results and summaries exclude image payloads, raw OCR text, clean text, translated text, secrets, endpoint credentials, and private debug paths in tests/unit/test_benchmark_logging_privacy.py

### Implementation for User Story 1

- [X] T022 [US1] Populate tests/benchmark/manifest.json with at least 12 safe local samples and labels covering Arabic, English, mixed text, book page, printed document, medicine package, receipt, sign, low light, angled image, far image, and blurry image
- [X] T023 [P] [US1] Add safe local benchmark sample fixtures in tests/benchmark/samples/ for all sample IDs referenced by tests/benchmark/manifest.json
- [X] T024 [P] [US1] Add expected text references in tests/benchmark/expected/ for all normal-quality Arabic, English, and mixed samples and at least 50 percent of difficult scenario samples
- [X] T025 [US1] Implement BenchmarkRunner sample iteration, OCR boundary invocation, image-quality rejection handling, result creation, duration recording, and run status aggregation in modules/benchmark/runner.py
- [X] T026 [US1] Integrate BenchmarkRunner with result writing so one run creates results.json, summary.json, and known_failures.md under benchmark_results/<run-id>/ in modules/benchmark/runner.py and modules/benchmark/result_writer.py
- [X] T027 [US1] Implement safe benchmark summary aggregation by scenario, language, success count, failure count, unavailable count, and evaluated OCR path in modules/benchmark/result_writer.py
- [X] T028 [US1] Wire scripts/benchmark_ocr.py to load tests/benchmark/manifest.json, execute BenchmarkRunner, print safe summary output, and return nonzero only for run-level failures
- [X] T029 [US1] Run focused US1 validation with python -m pytest tests/unit/test_benchmark_models.py tests/unit/test_benchmark_dataset_loader.py tests/unit/test_benchmark_expected_text.py tests/unit/test_benchmark_runner.py tests/unit/test_benchmark_result_writer.py tests/unit/test_benchmark_logging_privacy.py tests/integration/test_benchmark_workflow.py

**Checkpoint**: User Story 1 is independently functional as the MVP benchmark workflow.

---

## Phase 4: User Story 2 - Compare Engine Behavior Per Scenario (Priority: P2)

**Goal**: Compare existing OCR paths per benchmark sample and identify best-performing paths by scenario while continuing through unavailable or failed paths.

**Independent Test**: Run the benchmark in comparison mode with mocked OCR.space, PaddleOCR, Tesseract, cascade, unavailable online OCR, and unavailable local OCR outcomes; verify per-path results and best-path summaries.

### Tests for User Story 2

- [X] T030 [P] [US2] Write failing runner tests for separate OCR path measurement of ocr_space, paddleocr, tesseract, and cascade without changing normal assistant workflow behavior in tests/unit/test_benchmark_runner.py
- [X] T031 [P] [US2] Write failing tests for online OCR disabled, online OCR unavailable, local OCR unavailable, path timeout, weak OCR result, no text detected, and continuation through remaining paths in tests/unit/test_benchmark_runner.py
- [X] T032 [P] [US2] Write failing result summary tests for best_paths_by_scenario, per-engine success counts, per-engine duration summaries, per-engine quality summaries, and unavailable-path counts in tests/unit/test_benchmark_result_writer.py
- [X] T033 [P] [US2] Extend integration tests for mocked multi-path comparison mode and offline mode in tests/integration/test_benchmark_workflow.py
- [X] T034 [P] [US2] Write failing scope-boundary tests proving Phase 10 does not add OCR engines, translation engines, STT/TTS engines, assistant command categories, live assistant startup, cloud storage, paid services, user accounts, or deployment services in tests/unit/test_benchmark_scope_boundaries.py

### Implementation for User Story 2

- [X] T035 [US2] Implement requested OCR path resolution, offline path filtering, unavailable-path result creation, and sequential path execution in modules/benchmark/runner.py
- [X] T036 [US2] Implement adapter helpers that convert existing OCRResult, OCRCascadeResult, OCRQualityReport, and exception outcomes into BenchmarkResult records in modules/benchmark/runner.py
- [X] T037 [US2] Implement timeout, weak OCR, no-text, rejected image, engine-unavailable, online-unavailable, and unexpected-failure category mapping in modules/benchmark/benchmark_models.py and modules/benchmark/runner.py
- [X] T038 [US2] Implement best-path selection by scenario using expected_match_score first, quality_score second, success status third, and duration as tie-breaker in modules/benchmark/result_writer.py
- [X] T039 [US2] Ensure scripts/benchmark_ocr.py supports --paths and --offline while preserving safe output and no live assistant startup in scripts/benchmark_ocr.py
- [X] T040 [US2] Run focused US2 validation with python -m pytest tests/unit/test_benchmark_runner.py tests/unit/test_benchmark_result_writer.py tests/unit/test_benchmark_scope_boundaries.py tests/integration/test_benchmark_workflow.py

**Checkpoint**: User Stories 1 and 2 work independently and together.

---

## Phase 5: User Story 3 - Tune Thresholds From Evidence (Priority: P3)

**Goal**: Produce evidence-based tuning recommendations for image quality, OCR quality, preprocessing, and frame selection without automatically accepting unsafe threshold changes.

**Independent Test**: Run tuning analysis against controlled benchmark result sets and verify recommendations cite evidence, list affected scenarios, document expected benefit, document regression risk, and remain unaccepted when evidence is missing or normal Arabic, English, or mixed samples regress.

### Tests for User Story 3

- [X] T041 [P] [US3] Write failing tuning tests for generating recommendations from successful, weak, rejected, and failed benchmark results in tests/unit/test_benchmark_tuning.py
- [X] T042 [P] [US3] Write failing tuning gate tests for missing evidence, unresolved tradeoffs, normal Arabic regression, normal English regression, normal mixed regression, and accepted=false defaults in tests/unit/test_benchmark_tuning.py
- [X] T043 [P] [US3] Write failing result summary tests proving tuning recommendations are serialized without raw OCR text, clean text, image payloads, secrets, or private debug paths in tests/unit/test_benchmark_logging_privacy.py
- [X] T044 [P] [US3] Extend integration tests for benchmark run plus tuning recommendation output in summary.json in tests/integration/test_benchmark_workflow.py

### Implementation for User Story 3

- [X] T045 [US3] Implement TuningRecommendation creation, evidence grouping by target_area, affected scenario extraction, expected benefit summaries, and regression risk summaries in modules/benchmark/tuning.py
- [X] T046 [US3] Implement acceptance gate logic that blocks recommendations with missing evidence, undocumented tradeoffs, or regressions in normal Arabic, English, or mixed samples in modules/benchmark/tuning.py
- [X] T047 [US3] Integrate tuning analysis into BenchmarkRunner and summary.json generation without applying threshold changes automatically in modules/benchmark/runner.py and modules/benchmark/result_writer.py
- [X] T048 [US3] Add safe tuning recommendation output to known_failures.md or summary.json without exposing private text or image content in modules/benchmark/result_writer.py
- [X] T049 [US3] Run focused US3 validation with python -m pytest tests/unit/test_benchmark_tuning.py tests/unit/test_benchmark_logging_privacy.py tests/integration/test_benchmark_workflow.py

**Checkpoint**: User Stories 1, 2, and 3 work independently and together.

---

## Phase 6: User Story 4 - Document Known OCR Failure Cases (Priority: P4)

**Goal**: Document benchmark methodology, best paths, known failure cases, privacy behavior, and reproducible interpretation guidance for future contributors.

**Independent Test**: Review generated and maintained docs to verify dataset categories, expected-text policy, comparison normalization, result fields, privacy behavior, best-path interpretation, tuning recommendation rules, and known failure reporting are complete and reproducible.

### Tests for User Story 4

- [X] T050 [P] [US4] Write failing tests for known failure case generation from rejected image, weak OCR, no text, engine unavailable, path timeout, and unexpected benchmark failure in tests/unit/test_benchmark_result_writer.py
- [X] T051 [P] [US4] Write failing documentation contract tests that verify docs/benchmark_methodology.md includes dataset policy, expected-text policy, normalization policy, result fields, privacy behavior, tuning gates, and known failure interpretation in tests/unit/test_benchmark_scope_boundaries.py
- [X] T052 [P] [US4] Extend privacy tests proving known_failures.md and docs examples exclude private raw OCR text, clean text, image payloads, translated text, secrets, and debug paths in tests/unit/test_benchmark_logging_privacy.py

### Implementation for User Story 4

- [X] T053 [US4] Implement known failure case extraction and grouped known_failures.md rendering in modules/benchmark/result_writer.py
- [X] T054 [US4] Update docs/benchmark_methodology.md with Phase 10 dataset categories, manifest format, expected-text coverage, comparison normalization, result interpretation, best-path summary, tuning gates, privacy policy, and known failure reporting
- [X] T055 [US4] Update tests/benchmark/README.md with safe fixture policy, sample-label policy, expected-text policy, manual sample policy, and no-private-content guidance
- [X] T056 [US4] Update specs/011-phase10-benchmarking-accuracy-tuning/quickstart.md with final benchmark command examples, offline examples, generated artifact examples, and optional live OCR notes discovered during implementation
- [X] T057 [US4] Run focused US4 validation with python -m pytest tests/unit/test_benchmark_result_writer.py tests/unit/test_benchmark_scope_boundaries.py tests/unit/test_benchmark_logging_privacy.py

**Checkpoint**: All Phase 10 user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation alignment, privacy review, scope review, benchmark smoke checks, and regression checks across Phase 10.

- [X] T058 [P] Update docs/architecture.md with Phase 10 benchmark package boundaries, dataset lifecycle, result lifecycle, tuning recommendation lifecycle, and privacy behavior
- [X] T059 [P] Update docs/troubleshooting.md with Phase 10 benchmark dataset, engine unavailable, online unavailable, expected-text missing, result overwrite prevention, and optional live dependency guidance
- [X] T060 [P] Update specs/011-phase10-benchmarking-accuracy-tuning/contracts/benchmark-workflow-contract.md with final command flags, manifest fields, output fields, failure categories, and scope boundaries after implementation
- [X] T061 Run focused Phase 10 validation with python -m pytest tests/unit/test_benchmark_models.py tests/unit/test_benchmark_dataset_loader.py tests/unit/test_benchmark_expected_text.py tests/unit/test_benchmark_runner.py tests/unit/test_benchmark_result_writer.py tests/unit/test_benchmark_tuning.py tests/unit/test_benchmark_logging_privacy.py tests/unit/test_benchmark_scope_boundaries.py tests/integration/test_benchmark_workflow.py
- [X] T062 Run benchmark CLI smoke validation with python scripts/benchmark_ocr.py --dataset tests/benchmark/manifest.json --output-dir benchmark_results
- [X] T063 Run offline benchmark CLI smoke validation with python scripts/benchmark_ocr.py --dataset tests/benchmark/manifest.json --output-dir benchmark_results --offline
- [X] T064 Run full unit regression with python -m pytest tests/unit
- [X] T065 Run lint validation with python -m ruff check .
- [X] T066 Run optional formatting/type validation with python -m black --check . and python -m mypy . when installed
- [X] T067 Verify Phase 10 scope, privacy, dataset coverage, expected-text coverage, repeated-run retention, tuning gates, quickstart, and no-placeholder completion against specs/011-phase10-benchmarking-accuracy-tuning/quickstart.md
- [X] T068 Mark all completed tasks in specs/011-phase10-benchmarking-accuracy-tuning/tasks.md after validation succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational and can use mocked path outcomes, but final validation should include US1 result writing
- **User Story 3 (Phase 5)**: Depends on Foundational and can use controlled result fixtures, but final validation should include US1/US2 output shapes
- **User Story 4 (Phase 6)**: Depends on Foundational and can document controlled results, but final validation should include known failures from US1/US2/US3
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: Can be tested independently with mocked benchmark results, but integrates with US1 result writer
- **US3 (P3)**: Can be tested independently with controlled result fixtures, but integrates with US1/US2 summaries
- **US4 (P4)**: Can be tested independently with controlled known-failure inputs, but final docs should reflect US1/US2/US3 behavior

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Models before services
- Dataset and expected-text validation before runner integration
- Runner behavior before CLI smoke checks
- Result summaries before tuning and documentation
- Story-specific implementation before focused validation
- Validate each story before starting the next priority phase

### Parallel Opportunities

- T002, T003, T004, T005, and T006 can run in parallel after T001
- T009, T011, T013, and T015 can run in parallel after T007 establishes model expectations
- US1 tests T018, T019, T020, and T021 can run in parallel
- US2 tests T030, T031, T032, T033, and T034 can run in parallel
- US3 tests T041, T042, T043, and T044 can run in parallel
- US4 tests T050, T051, and T052 can run in parallel
- Polish documentation tasks T058, T059, and T060 can run in parallel after implementation stabilizes

---

## Parallel Example: User Story 1

```text
Task: "Write failing tests for controlled 12-sample manifest coverage, required language labels, required scenario labels, overlapping labels, and expected-text coverage in tests/unit/test_benchmark_dataset_loader.py"
Task: "Write failing tests for benchmark run orchestration over all samples with mocked OCR success, mocked OCR weak output, mocked image rejection, and structured per-sample results in tests/unit/test_benchmark_runner.py"
Task: "Write failing integration test for one full mocked benchmark run from tests/benchmark/manifest.json to timestamped benchmark_results output in tests/integration/test_benchmark_workflow.py"
Task: "Write failing privacy tests proving benchmark results and summaries exclude image payloads, raw OCR text, clean text, translated text, secrets, endpoint credentials, and private debug paths in tests/unit/test_benchmark_logging_privacy.py"
```

## Parallel Example: User Story 2

```text
Task: "Write failing runner tests for separate OCR path measurement of ocr_space, paddleocr, tesseract, and cascade without changing normal assistant workflow behavior in tests/unit/test_benchmark_runner.py"
Task: "Write failing tests for online OCR disabled, online OCR unavailable, local OCR unavailable, path timeout, weak OCR result, no text detected, and continuation through remaining paths in tests/unit/test_benchmark_runner.py"
Task: "Write failing result summary tests for best_paths_by_scenario, per-engine success counts, per-engine duration summaries, per-engine quality summaries, and unavailable-path counts in tests/unit/test_benchmark_result_writer.py"
Task: "Extend integration tests for mocked multi-path comparison mode and offline mode in tests/integration/test_benchmark_workflow.py"
Task: "Write failing scope-boundary tests proving Phase 10 does not add OCR engines, translation engines, STT/TTS engines, assistant command categories, live assistant startup, cloud storage, paid services, user accounts, or deployment services in tests/unit/test_benchmark_scope_boundaries.py"
```

## Parallel Example: User Story 3

```text
Task: "Write failing tuning tests for generating recommendations from successful, weak, rejected, and failed benchmark results in tests/unit/test_benchmark_tuning.py"
Task: "Write failing tuning gate tests for missing evidence, unresolved tradeoffs, normal Arabic regression, normal English regression, normal mixed regression, and accepted=false defaults in tests/unit/test_benchmark_tuning.py"
Task: "Write failing result summary tests proving tuning recommendations are serialized without raw OCR text, clean text, image payloads, secrets, or private debug paths in tests/unit/test_benchmark_logging_privacy.py"
Task: "Extend integration tests for benchmark run plus tuning recommendation output in summary.json in tests/integration/test_benchmark_workflow.py"
```

## Parallel Example: User Story 4

```text
Task: "Write failing tests for known failure case generation from rejected image, weak OCR, no text, engine unavailable, path timeout, and unexpected benchmark failure in tests/unit/test_benchmark_result_writer.py"
Task: "Write failing documentation contract tests that verify docs/benchmark_methodology.md includes dataset policy, expected-text policy, normalization policy, result fields, privacy behavior, tuning gates, and known failure interpretation in tests/unit/test_benchmark_scope_boundaries.py"
Task: "Extend privacy tests proving known_failures.md and docs examples exclude private raw OCR text, clean text, image payloads, translated text, secrets, and debug paths in tests/unit/test_benchmark_logging_privacy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation for benchmark models, manifest loading, expected-text comparison, result writing, and CLI contract.
3. Complete Phase 3 US1 local controlled benchmark run.
4. Stop and validate US1 independently with mocked OCR outcomes and timestamped local outputs.

### Incremental Delivery

1. Deliver US1 so the controlled dataset can be benchmarked repeatably.
2. Add US2 path comparison and best-path summaries.
3. Add US3 evidence-based tuning recommendations with acceptance gates.
4. Add US4 methodology and known failure documentation.
5. Complete quickstart alignment, privacy review, lint, optional formatting/type checks, CLI smoke runs, and full unit regression.

### Quality Gates

- No task may introduce new OCR engines, translation engines, STT/TTS engines, assistant command categories, paid services, cloud storage, user accounts, visual UI, deployment services, or live assistant startup in benchmark code.
- Benchmark results must be timestamped and must not overwrite prior runs by default.
- Default benchmark outputs must never include image payloads, raw OCR text, clean text, translated text, provider secrets, endpoint credentials, or private debug artifact paths.
- Dataset validation must prove at least 12 safe local samples and all required language/scenario coverage.
- Expected-text references must cover all normal-quality language samples and at least 50 percent of difficult scenario samples.
- Tuning recommendations must remain evidence-only unless measured evidence, tradeoffs, and no-regression gates pass.
