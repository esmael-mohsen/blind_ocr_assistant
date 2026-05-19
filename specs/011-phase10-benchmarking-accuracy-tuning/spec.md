# Feature Specification: Phase 10 Benchmarking and Accuracy Tuning

**Feature Branch**: `011-phase10-benchmarking-accuracy-tuning`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 10 with best practices"

## Clarifications

### Session 2026-05-18

- Q: What is the minimum controlled benchmark dataset for Phase 10? -> A: Use at least 12 safe local samples, with overlapping labels allowed, covering Arabic, English, mixed text, and every required real-world scenario.
- Q: Which samples require expected-text references for objective quality comparison? -> A: Require expected-text references for all normal-quality language samples and at least 50% of difficult scenario samples, including at least one Arabic, one English, and one mixed reference.
- Q: How should benchmark outputs handle repeated runs? -> A: Store each benchmark run as a separate timestamped local result set; do not overwrite prior results by default.
- Q: When may a tuning recommendation be accepted? -> A: Accept only when measured evidence improves or explains a target scenario, documents tradeoffs, and shows no regression for normal Arabic, English, or mixed samples.
- Q: How should expected-text comparison treat formatting differences? -> A: Normalize whitespace and line-break differences for comparison while preserving language-bearing characters, numbers, and meaningful punctuation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Benchmark Real-World OCR Scenarios (Priority: P1)

As a maintainer, I need a repeatable benchmark set for Arabic, English, and mixed real-world text so OCR quality decisions can be measured instead of guessed.

**Why this priority**: Accurate reading is the core assistive promise. Before tuning thresholds, the project needs representative evidence across common blind-user reading scenarios.

**Independent Test**: Run the benchmark against a controlled sample set with expected text references and verify that every sample produces a result record with scenario type, language category, duration, text length, quality score, selected or tested engine, fallback status, and failure category when applicable.

**Acceptance Scenarios**:

1. **Given** at least 12 safe local benchmark samples for Arabic, English, mixed text, and required real-world scenarios are available, **When** the benchmark is run, **Then** each sample is evaluated and recorded with measurable OCR quality and duration outcomes.
2. **Given** samples include book pages, printed documents, medicine packages, receipts, signs, low-light captures, angled captures, far captures, and blurry captures, **When** results are reviewed, **Then** maintainers can compare performance by scenario without manually opening image previews.
3. **Given** an expected-text reference exists for a selected sample, **When** OCR output is produced, **Then** the benchmark records a comparable quality outcome without writing private text into default logs.

---

### User Story 2 - Compare Engine Behavior Per Scenario (Priority: P2)

As a maintainer, I need OCR engines and cascade choices compared per scenario so the assistant can choose the most reliable path for Arabic, English, mixed, and difficult captures.

**Why this priority**: The assistant already has multiple OCR paths. Phase 10 must expose which path performs best under realistic conditions before tuning fallback thresholds.

**Independent Test**: Run the benchmark in engine-comparison mode against the controlled dataset and verify that results identify success, weak output, duration, quality, and failure reason for each configured OCR path.

**Acceptance Scenarios**:

1. **Given** a benchmark sample and available OCR paths, **When** the comparison is run, **Then** results show the measured outcome for each path without changing the normal user workflow.
2. **Given** one path fails or is unavailable, **When** other paths can still run, **Then** the benchmark records the failed path and continues with remaining paths.
3. **Given** online OCR is unavailable, **When** a benchmark run is requested, **Then** local paths are measured and the missing online path is recorded as unavailable rather than blocking the whole benchmark.

---

### User Story 3 - Tune Thresholds From Evidence (Priority: P3)

As a maintainer, I need tuning recommendations based on benchmark results so image quality, OCR quality, and frame selection thresholds improve accuracy without silently lowering standards.

**Why this priority**: Threshold changes affect what blind users hear. They must be justified by measured accuracy, not subjective impressions.

**Independent Test**: Run tuning analysis on a benchmark result set and verify it reports recommended threshold adjustments, affected scenarios, expected benefit, regression risks, and cases that should remain unchanged.

**Acceptance Scenarios**:

1. **Given** benchmark results contain successful and failed samples, **When** tuning analysis is run, **Then** it identifies candidate changes for quality thresholds and explains the evidence behind each recommendation.
2. **Given** a candidate tuning change would improve one scenario but harm another, **When** the recommendation is produced, **Then** the tradeoff is documented before any threshold is accepted.
3. **Given** evidence is insufficient for a threshold change, **When** tuning analysis is run, **Then** the system reports no change rather than making an unsupported adjustment.

---

### User Story 4 - Document Known OCR Failure Cases (Priority: P4)

As a maintainer, I need benchmark findings documented in a practical methodology and failure-case report so future OCR changes can be compared against the same baseline.

**Why this priority**: Benchmarks are useful only if future contributors can reproduce them and understand the known limits of the assistant.

**Independent Test**: Review the benchmark methodology and results summary and verify they explain dataset categories, expected-text policy, privacy limits, result fields, tuning interpretation, and known failure cases.

**Acceptance Scenarios**:

1. **Given** benchmark results have been produced, **When** documentation is generated or updated, **Then** it identifies best-performing paths by scenario and known weak cases.
2. **Given** a user-content sample contains private text, **When** benchmark documentation is prepared, **Then** private raw OCR text and clean text are excluded unless explicitly marked as safe fixture content.
3. **Given** a later phase or contributor wants to repeat the benchmark, **When** they read the methodology, **Then** they can reproduce the benchmark conditions and interpret the output.

### Edge Cases

- Benchmark dataset is missing, empty, or contains unsupported files.
- Expected-text references are missing for some samples.
- A sample is intentionally poor quality and should fail quality checks rather than be forced through OCR.
- Online OCR is disabled, unavailable, slow, rate-limited, or returns an error.
- Local OCR engines are not installed or cannot load on the current machine.
- Benchmark samples include mixed Arabic and English text, numerals, prices, signs, package labels, small fonts, glare, blur, angle, distance, or low light.
- Benchmark runs are interrupted before completion.
- Result files from previous runs already exist.
- Multiple benchmark runs are executed on the same day and must remain distinguishable.
- Debug image saving or sensitive text logging is disabled.
- A tuning recommendation improves average quality but increases failures for Arabic, English, mixed, or accessibility-critical scenarios.
- Expected-text comparison includes harmless spacing differences, line-break differences, Arabic punctuation, English punctuation, numbers, prices, or mixed-language tokens.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a repeatable OCR benchmark workflow covering Arabic, English, mixed text, and difficult real-world capture scenarios.
- **FR-002**: System MUST include at least 12 safe local benchmark samples with sample labels covering book pages, printed documents, medicine packages, receipts, signs, low light, angled images, far images, blurry images, Arabic, English, and mixed text; one sample MAY satisfy multiple labels.
- **FR-003**: System MUST support expected-text references for all normal-quality language samples and at least 50% of difficult scenario samples so OCR quality can be compared consistently.
- **FR-004**: System MUST record benchmark results with scenario category, language category, engine or path name, success status, duration, text length, quality score, fallback status, and failure category.
- **FR-005**: System MUST allow OCR paths to be measured separately without changing the normal assistant workflow behavior.
- **FR-006**: System MUST continue benchmark execution when one OCR path is unavailable or fails, as long as other requested paths can still be evaluated.
- **FR-007**: System MUST distinguish unavailable engines, weak OCR output, no-text results, rejected image quality, and unexpected benchmark failures.
- **FR-008**: System MUST evaluate image-quality, OCR-quality, and frame-selection outcomes against benchmark evidence before recommending threshold changes.
- **FR-009**: System MUST document each tuning recommendation with affected scenarios, measured evidence, expected benefit, and regression risk.
- **FR-010**: System MUST avoid applying threshold changes automatically when evidence is insufficient, tradeoffs are unresolved, or normal Arabic, English, or mixed samples regress.
- **FR-011**: System MUST document known failure cases discovered by benchmark runs, including guidance for whether the issue is capture quality, OCR routing, preprocessing, language handling, or engine limitation.
- **FR-012**: System MUST keep benchmark artifacts local by default and MUST NOT introduce cloud storage, user accounts, paid benchmark services, or mandatory online dependencies.
- **FR-013**: System MUST exclude private image content, raw OCR text, clean text, and translated text from default logs and summary reports unless the content is an explicit safe fixture or debug mode is enabled.
- **FR-014**: System MUST support benchmark runs on development machines with mocked or unavailable hardware and on target hardware when manual image capture samples are available.
- **FR-015**: System MUST provide a clear pass/fail benchmark summary that maintainers can use before accepting OCR-related threshold or routing changes.
- **FR-016**: System MUST preserve the existing accessibility-first behavior by treating poor images and weak OCR as measurable failures that should lead to guidance or fallback, not silent acceptance.
- **FR-017**: System MUST keep normal read and translation workflows operationally separate from benchmark runs so benchmarking cannot accidentally start live assistant sessions.
- **FR-018**: System MUST make benchmark output comparable across runs by using stable scenario labels, stable result fields, and explicit environment notes.
- **FR-019**: System MUST keep repeated benchmark runs as separate timestamped local result sets and MUST NOT overwrite prior results by default.
- **FR-020**: System MUST compare OCR output against expected text using a documented normalization policy that ignores harmless whitespace and line-break differences while preserving language-bearing characters, numbers, and meaningful punctuation.

### Constitution Requirements

- **CR-001**: Feature MUST be usable for validation without visual confirmation by producing accessible summaries and clear pass/fail outcomes.
- **CR-002**: Feature MUST document OCR fallback behavior and engine comparison outcomes because it measures OCR routing and quality decisions.
- **CR-003**: Feature MUST avoid paid-service dependency and treat online services as optional and replaceable during benchmark runs.
- **CR-004**: Feature MUST define privacy behavior for benchmark images, expected text, OCR output, logs, debug artifacts, and result summaries.
- **CR-005**: Feature MUST define measurable benchmark criteria for Arabic, English, mixed text, blur, lighting, angle, distance, small fonts, and relevant OCR failure modes.

### Key Entities *(include if feature involves data)*

- **BenchmarkDataset**: A local collection of benchmark samples grouped by scenario, language category, and expected-text availability.
- **BenchmarkSample**: One image or capture fixture with scenario labels, language labels, optional expected text reference, and privacy classification.
- **ExpectedTextReference**: A safe fixture text file or reference value used to compare OCR output for selected samples.
- **BenchmarkRun**: One timestamped execution of the benchmark with environment notes, requested OCR paths, start/end status, and summary metrics.
- **BenchmarkResult**: One measured result for one sample and one OCR path, including duration, quality score, text length, success state, fallback status, and failure category.
- **TuningRecommendation**: A proposed threshold or scoring adjustment with supporting evidence, affected scenarios, expected benefit, and regression risk.
- **KnownFailureCase**: A documented recurring failure pattern with scenario labels, likely cause, user impact, and recommended follow-up.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of benchmark samples in the controlled dataset produce a result record or a structured unavailable/failure record.
- **SC-002**: Benchmark coverage includes at least 12 safe local samples and at least one Arabic, one English, and one mixed-language sample for normal-quality text.
- **SC-003**: Benchmark coverage includes at least one sample label each for book page, printed document, medicine package, receipt, sign, low light, angled image, far image, and blurry image scenarios.
- **SC-004**: 100% of result records include scenario category, language category, measured duration, text length, quality score or failure category, and evaluated OCR path.
- **SC-005**: 100% of engine-unavailable or online-unavailable cases are recorded as structured outcomes without stopping unrelated benchmark cases.
- **SC-006**: 100% of tuning recommendations cite measured evidence and list affected scenarios before any threshold change is accepted.
- **SC-007**: 0 tuning recommendations are accepted when benchmark evidence is missing, regression risk is undocumented, or normal Arabic, English, or mixed samples regress.
- **SC-008**: 100% of default benchmark logs and summaries exclude private raw OCR text, clean text, translated text, image payloads, secrets, and debug artifact paths.
- **SC-009**: Benchmark methodology documentation explains dataset categories, expected-text policy, result interpretation, privacy behavior, and known failure-case reporting.
- **SC-010**: Maintainers can identify the best-performing OCR path for each benchmark scenario from the result summary.
- **SC-011**: At least one known failure-case report is produced when any benchmark sample fails quality, OCR, or comparison expectations.
- **SC-012**: Re-running the same benchmark dataset under the same environment produces comparable result fields and scenario labels for 100% of samples.
- **SC-013**: 100% of repeated benchmark runs create separate local result sets without overwriting previous run artifacts by default.
- **SC-014**: 100% of expected-text comparisons apply the documented normalization policy consistently across Arabic, English, and mixed samples.

## Assumptions

- Phase 0 through Phase 9 provide the OCR engines, image-quality checks, preprocessing variants, frame selection, OCR cascade, text cleanup, logging policy, and workflow boundaries needed for measurement.
- Phase 10 measures and tunes existing behavior; it does not add new OCR engines, paid services, user accounts, visual UI, cloud storage, deployment services, or normal assistant command categories.
- Benchmark images are local fixtures or explicitly collected manual samples. Private real-world content is not committed unless it is sanitized and intentionally marked as safe fixture data.
- Expected-text references are required for all normal-quality language samples and at least half of difficult scenario samples; samples without references can still record duration, success/failure, text length, and quality metadata.
- Threshold tuning recommendations are generated as evidence for maintainers and are not automatically applied when tradeoffs are unclear.
- Live online OCR may be unavailable during automated development, so benchmark behavior must still produce useful local or unavailable-path results.
- Hardware-dependent benchmark collection is optional for automated tests and can be documented as manual acceptance when target camera hardware is unavailable.
