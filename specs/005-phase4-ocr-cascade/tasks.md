# Tasks: Phase 4 OCR Cascade Controller

**Input**: Design documents from `/specs/005-phase4-ocr-cascade/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Automated tests are required by the accepted specification and constitution for OCR quality thresholds, cascade fallback paths, offline routing, High Accuracy Mode, one-attempt limits, image-not-ready blocking, privacy-safe logging, and Phase 4 scope boundaries. Write story tests before implementation and confirm they fail for the intended missing behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- All descriptions include exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 4 module files, fixture notes, and cascade configuration defaults.

- [X] T001 Create Phase 4 OCR cascade module placeholder in modules/ocr/ocr_cascade.py
- [X] T002 Create Phase 4 OCR quality module placeholder in modules/ocr/ocr_quality.py
- [X] T003 [P] Create OCR quality fixture notes in tests/fixtures/text/ocr_quality_cases.md
- [X] T004 Add Phase 4 OCR cascade exports to modules/ocr/__init__.py
- [X] T005 Add Phase 4 defaults to config.py for OCR quality threshold, one-attempt engine limit, High Accuracy score tie delta, online availability timeout, and sensitive text logging behavior

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared cascade models, stable errors, privacy helpers, and OCR quality primitives needed by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 [P] Add failing model tests for OCRCascadeRequest validation, image-ready blocking fields, and one-attempt defaults in tests/unit/test_ocr_cascade_models.py
- [X] T007 [P] Add failing model tests for OCRAttempt, OCRQualityReport, OCRCascadeResult, OCRCascadeError, and safe metadata in tests/unit/test_ocr_cascade_models.py
- [X] T008 Define OCR cascade error codes, attempt status enum, route mode enum, and language mix enum in modules/ocr/ocr_cascade.py
- [X] T009 Implement OCRCascadeRequest model with image_ready_for_ocr, allow_online, allow_offline, high_accuracy, quality_threshold, max_attempts_per_engine, and sensitive_text_logging_enabled in modules/ocr/ocr_cascade.py
- [X] T010 Implement OCRAttempt, OCRCascadeResult, and OCRCascadeError models with safe metadata and stable validation in modules/ocr/ocr_cascade.py
- [X] T011 Implement OCRQualityReport and issue categories in modules/ocr/ocr_quality.py
- [X] T012 Implement OCR cascade metadata sanitization that excludes raw OCR text, clean text, image contents, uploaded payloads, secrets, and debug paths in modules/ocr/ocr_cascade.py
- [X] T013 Export foundational Phase 4 models and quality report types from modules/ocr/__init__.py
- [X] T014 Run foundational validation with python -m pytest tests/unit/test_ocr_cascade_models.py

**Checkpoint**: OCR cascade data contracts, errors, and safe metadata are ready; user story implementation can begin.

---

## Phase 3: User Story 1 - Choose the Best OCR Result Through Fallback (Priority: P1) MVP

**Goal**: Run the normal cascade so good online OCR is accepted, weak or failed online OCR falls back to local accuracy OCR, weak or failed local OCR falls back to emergency OCR, and all-engine failure returns structured guidance.

**Independent Test**: With mocked OCR engines, normal mode accepts a good online result without fallback, falls back on weak or failed results, attempts emergency OCR when local accuracy is weak, and returns a structured final failure only after all allowed engines fail or produce unacceptable text.

### Tests for User Story 1

- [X] T015 [P] [US1] Add failing OCR quality test for accepting quality scores of 0.70 or higher and rejecting scores below 0.70 in tests/unit/test_ocr_quality.py
- [X] T016 [P] [US1] Add failing OCR quality tests for empty, very short, symbol-heavy, repeated-character, excessive-spacing, Arabic, English, and mixed-language cases in tests/unit/test_ocr_quality.py
- [X] T017 [P] [US1] Add failing cascade test for accepting good online OCR without attempting fallback engines in tests/unit/test_ocr_cascade.py
- [X] T018 [P] [US1] Add failing cascade test for weak online OCR triggering local accuracy fallback in tests/unit/test_ocr_cascade.py
- [X] T019 [P] [US1] Add failing cascade test for weak local accuracy OCR triggering emergency OCR fallback in tests/unit/test_ocr_cascade.py
- [X] T020 [P] [US1] Add failing cascade test for all allowed engines failing with ALL_OCR_ENGINES_FAILED guidance in tests/unit/test_ocr_cascade.py

### Implementation for User Story 1

- [X] T021 [US1] Implement deterministic OCR quality scoring heuristics and threshold handling in modules/ocr/ocr_quality.py
- [X] T022 [US1] Implement Arabic, English, and mixed-language detection support for OCR quality decisions in modules/ocr/ocr_quality.py
- [X] T023 [US1] Implement normal cascade engine ordering and mocked engine adapter handling in modules/ocr/ocr_cascade.py
- [X] T024 [US1] Implement online primary acceptance without fallback when OCR quality is acceptable in modules/ocr/ocr_cascade.py
- [X] T025 [US1] Implement weak-result and failure fallback from online primary to local accuracy OCR in modules/ocr/ocr_cascade.py
- [X] T026 [US1] Implement weak-result and failure fallback from local accuracy OCR to emergency OCR in modules/ocr/ocr_cascade.py
- [X] T027 [US1] Implement structured final failure with stable errors and guidance when no allowed OCR result is acceptable in modules/ocr/ocr_cascade.py
- [X] T028 [US1] Export run_ocr_cascade and assess_ocr_quality APIs from modules/ocr/__init__.py
- [X] T029 [US1] Run User Story 1 validation with python -m pytest tests/unit/test_ocr_quality.py tests/unit/test_ocr_cascade.py

**Checkpoint**: User Story 1 is independently complete and provides the Phase 4 MVP.

---

## Phase 4: User Story 2 - Continue Reading When Internet Is Unavailable (Priority: P2)

**Goal**: Skip online OCR when internet is unavailable, disabled, or disallowed, then run local accuracy OCR before emergency OCR while recording offline routing.

**Independent Test**: With mocked online availability and OCR engines, the cascade skips online OCR, does not upload user images, attempts local accuracy first, falls back to emergency OCR when needed, and records offline route metadata.

### Tests for User Story 2

- [X] T030 [P] [US2] Add failing cascade test for skipping online OCR when online availability check is unavailable in tests/unit/test_ocr_cascade.py
- [X] T031 [P] [US2] Add failing cascade test for skipping online OCR when allow_online is false in tests/unit/test_ocr_cascade.py
- [X] T032 [P] [US2] Add failing cascade test for online availability timeout routing to local accuracy fallback in tests/unit/test_ocr_cascade.py
- [X] T033 [P] [US2] Add failing cascade test for local accuracy failure offline triggering emergency OCR in tests/unit/test_ocr_cascade.py
- [X] T034 [P] [US2] Add failing cascade test for each allowed engine being attempted at most once per cascade request in tests/unit/test_ocr_cascade.py

### Implementation for User Story 2

- [X] T035 [US2] Implement online availability provider contract and short timeout handling in modules/ocr/ocr_cascade.py
- [X] T036 [US2] Implement offline route selection when allow_online is false or online availability fails in modules/ocr/ocr_cascade.py
- [X] T037 [US2] Implement local accuracy first and emergency fallback second ordering for offline route in modules/ocr/ocr_cascade.py
- [X] T038 [US2] Implement one-attempt-per-engine default enforcement and attempt counting in modules/ocr/ocr_cascade.py
- [X] T039 [US2] Add offline_route_used, skipped online attempt, and fallback metadata to OCRCascadeResult in modules/ocr/ocr_cascade.py
- [X] T040 [US2] Run User Story 2 validation with python -m pytest tests/unit/test_ocr_cascade.py

**Checkpoint**: User Story 2 is independently complete and offline degraded OCR routing works with mocked engines.

---

## Phase 5: User Story 3 - Compare Results in High Accuracy Mode (Priority: P3)

**Goal**: In High Accuracy Mode, compare available online primary and local accuracy results, select the higher-quality acceptable result, prefer local accuracy for similar scores within 0.05, and use emergency OCR only when both compared candidates fail or are weak.

**Independent Test**: With mocked high-accuracy OCR outcomes, the cascade compares online and local accuracy candidates, selects the correct result by quality and tie-break rules, skips online comparison while offline, and attempts emergency OCR only when needed.

### Tests for User Story 3

- [X] T041 [P] [US3] Add failing High Accuracy Mode test for comparing online primary and local accuracy candidates before selection in tests/unit/test_ocr_cascade.py
- [X] T042 [P] [US3] Add failing High Accuracy Mode test for selecting the higher-quality acceptable OCR result in tests/unit/test_ocr_cascade.py
- [X] T043 [P] [US3] Add failing High Accuracy Mode test for preferring local accuracy when acceptable scores differ by less than 0.05 in tests/unit/test_ocr_cascade.py
- [X] T044 [P] [US3] Add failing High Accuracy Mode test for using shorter duration only as the final tie-breaker in tests/unit/test_ocr_cascade.py
- [X] T045 [P] [US3] Add failing High Accuracy Mode test for attempting emergency OCR only when compared primary candidates fail or are weak in tests/unit/test_ocr_cascade.py
- [X] T046 [P] [US3] Add failing High Accuracy Mode offline test for skipping online comparison and using local candidates in tests/unit/test_ocr_cascade.py

### Implementation for User Story 3

- [X] T047 [US3] Implement High Accuracy Mode candidate collection for online primary and local accuracy OCR in modules/ocr/ocr_cascade.py
- [X] T048 [US3] Implement High Accuracy Mode quality comparison and acceptable-result filtering in modules/ocr/ocr_cascade.py
- [X] T049 [US3] Implement similar-score tie-break that prefers local accuracy within 0.05 in modules/ocr/ocr_cascade.py
- [X] T050 [US3] Implement shortest-duration final tie-break after quality and local-preference tie-breaks in modules/ocr/ocr_cascade.py
- [X] T051 [US3] Implement emergency OCR fallback only when high-accuracy compared candidates are failed or weak in modules/ocr/ocr_cascade.py
- [X] T052 [US3] Run User Story 3 validation with python -m pytest tests/unit/test_ocr_cascade.py

**Checkpoint**: User Story 3 is independently complete and High Accuracy Mode routing is deterministic.

---

## Phase 6: User Story 4 - Explain OCR Decisions Safely (Priority: P4)

**Goal**: Return and log safe cascade metadata including attempted engine path, selected engine, duration, quality score, fallback status, offline route status, high-accuracy status, and stable failure codes without exposing OCR text by default.

**Independent Test**: Successful, fallback, offline, high-accuracy, and failure scenarios return safe metadata and logs that exclude OCR text unless both debug mode and explicit sensitive-text logging are enabled.

### Tests for User Story 4

- [X] T053 [P] [US4] Add failing privacy test for safe cascade metadata excluding raw OCR text, clean text, image contents, uploaded payloads, secrets, and debug paths in tests/unit/test_ocr_cascade_logging_privacy.py
- [X] T054 [P] [US4] Add failing privacy test for default logs excluding OCR text in tests/unit/test_ocr_cascade_logging_privacy.py
- [X] T055 [P] [US4] Add failing privacy test for OCR text appearing in logs only when debug mode and sensitive-text logging are both enabled in tests/unit/test_ocr_cascade_logging_privacy.py
- [X] T056 [P] [US4] Add failing cascade metadata test for attempted path, selected engine, duration, quality score, fallback use, and failure code in tests/unit/test_ocr_cascade_logging_privacy.py

### Implementation for User Story 4

- [X] T057 [US4] Implement cascade safe metadata builder for attempts and results in modules/ocr/ocr_cascade.py
- [X] T058 [US4] Implement privacy-preserving cascade log metadata helpers in modules/ocr/ocr_cascade.py
- [X] T059 [US4] Implement sensitive-text logging gate requiring both debug mode and explicit sensitive-text logging in modules/ocr/ocr_cascade.py
- [X] T060 [US4] Ensure result guidance messages cover OCR progress, fallback, success, image-not-ready, and final failure paths in modules/ocr/ocr_cascade.py
- [X] T061 [US4] Run User Story 4 validation with python -m pytest tests/unit/test_ocr_cascade_logging_privacy.py tests/unit/test_ocr_cascade.py

**Checkpoint**: User Story 4 is independently complete and OCR cascade decisions are safely observable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify scope boundaries, documentation, quickstart validation, and whole-Phase 4 quality after all selected stories are complete.

- [X] T062 [P] Add Phase 4 scope-boundary tests preventing camera capture, best-frame selection, text cleanup, voice command, TTS, translation, and assistant workflow calls in tests/unit/test_ocr_cascade_scope_boundaries.py
- [X] T063 [P] Update docs/architecture.md with Phase 4 OCR quality, cascade routing, offline mode, High Accuracy Mode, privacy, and scope boundaries
- [X] T064 [P] Update docs/troubleshooting.md with weak OCR, all-engine failure, online OCR unavailable, image-not-ready, and sensitive logging guidance
- [X] T065 [P] Update quickstart validation notes in specs/005-phase4-ocr-cascade/quickstart.md with actual test commands and expected local-only behavior
- [X] T066 Run full Phase 4 unit validation with python -m pytest tests/unit
- [X] T067 Run optional quality validation with python -m ruff check .
- [X] T068 Run optional formatter/type checks when installed with python -m black --check . and python -m mypy .
- [X] T069 Mark completed tasks in specs/005-phase4-ocr-cascade/tasks.md after each task is implemented and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational and can build on US1 cascade execution while remaining independently testable with mocked offline routing.
- **User Story 3 (Phase 5)**: Depends on Foundational and uses US1 quality decisions; High Accuracy comparison can be tested with mocked engines.
- **User Story 4 (Phase 6)**: Depends on Foundational and observes all story paths; privacy helpers can be tested independently.
- **Polish (Phase 7)**: Depends on completed selected user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on US2, US3, or US4 after Foundational.
- **US2 (P2)**: Requires foundational request/result models and can reuse the US1 cascade attempt execution path.
- **US3 (P3)**: Requires foundational quality reports and US1-style attempt scoring.
- **US4 (P4)**: Can validate metadata helpers independently, then verify metadata across US1-US3 paths.

### Within Each User Story

- Tests must be written before implementation and fail for the missing behavior.
- Models and shared quality primitives must precede cascade services.
- Story-specific implementation must pass its independent validation command before moving to the next story.
- Privacy defaults, one-attempt limits, and Phase 4 scope boundaries must remain intact for every story.

## Parallel Opportunities

- Setup tasks T001-T003 can run in parallel because they touch different files.
- Foundational tests T006 and T007 can run in parallel before model implementation.
- US1 tests T015-T020 can be written in parallel because they cover distinct quality and cascade behaviors.
- US2 tests T030-T034 can be written in parallel because they cover distinct offline and retry behaviors.
- US3 tests T041-T046 can be written in parallel because they cover distinct High Accuracy Mode decisions.
- US4 tests T053-T056 can be written in parallel because they cover separate metadata and logging privacy paths.
- Polish docs T063-T065 can run in parallel with scope-boundary test T062.

## Parallel Example: User Story 1

```text
Task: "T015 [P] [US1] Add failing OCR quality test for accepting quality scores of 0.70 or higher and rejecting scores below 0.70 in tests/unit/test_ocr_quality.py"
Task: "T017 [P] [US1] Add failing cascade test for accepting good online OCR without attempting fallback engines in tests/unit/test_ocr_cascade.py"
Task: "T018 [P] [US1] Add failing cascade test for weak online OCR triggering local accuracy fallback in tests/unit/test_ocr_cascade.py"
Task: "T020 [P] [US1] Add failing cascade test for all allowed engines failing with ALL_OCR_ENGINES_FAILED guidance in tests/unit/test_ocr_cascade.py"
```

## Parallel Example: User Story 2

```text
Task: "T030 [P] [US2] Add failing cascade test for skipping online OCR when online availability check is unavailable in tests/unit/test_ocr_cascade.py"
Task: "T032 [P] [US2] Add failing cascade test for online availability timeout routing to local accuracy fallback in tests/unit/test_ocr_cascade.py"
Task: "T034 [P] [US2] Add failing cascade test for each allowed engine being attempted at most once per cascade request in tests/unit/test_ocr_cascade.py"
```

## Parallel Example: User Story 3

```text
Task: "T041 [P] [US3] Add failing High Accuracy Mode test for comparing online primary and local accuracy candidates before selection in tests/unit/test_ocr_cascade.py"
Task: "T043 [P] [US3] Add failing High Accuracy Mode test for preferring local accuracy when acceptable scores differ by less than 0.05 in tests/unit/test_ocr_cascade.py"
Task: "T046 [P] [US3] Add failing High Accuracy Mode offline test for skipping online comparison and using local candidates in tests/unit/test_ocr_cascade.py"
```

## Parallel Example: User Story 4

```text
Task: "T053 [P] [US4] Add failing privacy test for safe cascade metadata excluding raw OCR text, clean text, image contents, uploaded payloads, secrets, and debug paths in tests/unit/test_ocr_cascade_logging_privacy.py"
Task: "T055 [P] [US4] Add failing privacy test for OCR text appearing in logs only when debug mode and sensitive-text logging are both enabled in tests/unit/test_ocr_cascade_logging_privacy.py"
Task: "T056 [P] [US4] Add failing cascade metadata test for attempted path, selected engine, duration, quality score, fallback use, and failure code in tests/unit/test_ocr_cascade_logging_privacy.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational cascade models and OCR quality primitives.
3. Complete Phase 3 User Story 1 normal cascade fallback.
4. Validate with `python -m pytest tests/unit/test_ocr_quality.py tests/unit/test_ocr_cascade.py`.
5. Stop and confirm deterministic normal cascade routing before adding offline and high-accuracy behavior.

### Incremental Delivery

1. Setup plus foundational models.
2. US1 normal cascade fallback MVP.
3. US2 offline routing and one-attempt limits.
4. US3 High Accuracy Mode comparison.
5. US4 safe metadata and logging privacy.
6. Polish with scope-boundary tests, docs, full unit validation, and optional quality checks.

### Parallel Team Strategy

1. Complete Setup and Foundational phases together.
2. Implement US1 quality and normal cascade first.
3. After US1 execution path exists, split US2 offline routing, US3 high-accuracy comparison, and US4 metadata/privacy across separate files or coordinated sections.
4. Reserve final polish for cross-story scope, docs, and validation.

## Notes

- [P] tasks touch independent files or test cases and can be parallelized after their phase prerequisites.
- All OCR engine behavior in tests should use mocks; live OCR credentials and internet are not required.
- Do not introduce camera capture, best-frame selection, text cleanup, voice commands, TTS, translation, or full assistant workflow behavior in Phase 4.
- Keep OCR text out of default logs; allow text logging only when both debug mode and explicit sensitive-text logging are enabled.
