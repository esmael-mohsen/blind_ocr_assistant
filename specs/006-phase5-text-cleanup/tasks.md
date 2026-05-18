# Tasks: Phase 5 Text Cleanup, RTL Handling, and Language Detection

**Input**: Design documents from `/specs/006-phase5-text-cleanup/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Automated tests are required by the accepted specification and constitution for raw-text preservation, clean-text generation, whitespace and line-break normalization, punctuation spacing, conservative garbage cleanup, idempotence, Arabic/English/mixed readability, language evidence thresholds, RTL logical-order handling, privacy-safe logging, and Phase 5 scope boundaries. Write story tests before implementation and confirm they fail for the intended missing behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- All descriptions include exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 5 text module files, fixture notes, and exports.

- [X] T001 Create Phase 5 text cleanup module placeholder in modules/text/cleanup.py
- [X] T002 Create Phase 5 language detection module placeholder in modules/text/language_detector.py
- [X] T003 Create Phase 5 RTL utility module placeholder in modules/text/rtl_fixer.py
- [X] T004 [P] Create cleanup fixture notes in tests/fixtures/text/cleanup_cases.md
- [X] T005 [P] Create language detection fixture notes in tests/fixtures/text/language_detection_cases.md
- [X] T006 Add Phase 5 text exports to modules/text/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared text cleanup models, stable statuses, warnings, direction types, and safe metadata helpers needed by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 [P] Add failing model tests for TextCleanupRequest validation and raw-text preservation in tests/unit/test_text_cleanup_models.py
- [X] T008 [P] Add failing model tests for TextCleanupResult statuses, warnings, direction, guidance, and safe metadata in tests/unit/test_text_cleanup_models.py
- [X] T009 [P] Add failing model tests for LanguageDetectionResult evidence counts, confidence, dominant ratio, and direction in tests/unit/test_text_cleanup_models.py
- [X] T010 Define TextCleanupStatus, CleanupWarning, DetectedLanguage, and TextDirection enums in modules/text/cleanup.py
- [X] T011 Implement TextCleanupRequest and TextCleanupResult models with validation and text-free safe metadata in modules/text/cleanup.py
- [X] T012 Implement LanguageDetectionResult and DirectionInfo models in modules/text/language_detector.py
- [X] T013 Implement shared sensitive text metadata sanitization helpers in modules/text/cleanup.py
- [X] T014 Export foundational Phase 5 models and enums from modules/text/__init__.py
- [X] T015 Run foundational validation with python -m pytest tests/unit/test_text_cleanup_models.py

**Checkpoint**: Text cleanup data contracts and safe metadata primitives are ready; user story implementation can begin.

---

## Phase 3: User Story 1 - Read Clean OCR Text Aloud (Priority: P1) MVP

**Goal**: Preserve raw OCR text exactly while producing a separate clean text value with readable whitespace, line breaks, punctuation spacing, conservative garbage cleanup, idempotence, and guidance.

**Independent Test**: Provide noisy OCR text with extra spaces, broken lines, repeated whitespace, punctuation spacing issues, and ambiguous garbage fragments; verify raw text is unchanged and clean text is easier to read.

### Tests for User Story 1

- [X] T016 [P] [US1] Add failing cleanup test for preserving raw_text exactly while producing clean_text in tests/unit/test_text_cleanup.py
- [X] T017 [P] [US1] Add failing cleanup tests for repeated spaces, tabs, and simple whitespace normalization in tests/unit/test_text_cleanup.py
- [X] T018 [P] [US1] Add failing cleanup tests for collapsing single OCR line breaks while preserving blank-line paragraphs in tests/unit/test_text_cleanup.py
- [X] T019 [P] [US1] Add failing cleanup tests for preserving list-like line breaks in tests/unit/test_text_cleanup.py
- [X] T020 [P] [US1] Add failing cleanup tests for Arabic and English punctuation spacing normalization in tests/unit/test_text_cleanup.py
- [X] T021 [P] [US1] Add failing cleanup tests for conservative garbage cleanup preserving uncertain fragments with warnings in tests/unit/test_text_cleanup.py
- [X] T022 [P] [US1] Add failing cleanup tests for empty input, noisy status, guidance, and idempotence in tests/unit/test_text_cleanup.py

### Implementation for User Story 1

- [X] T023 [US1] Implement public clean_ocr_text entry point using TextCleanupRequest and TextCleanupResult in modules/text/cleanup.py
- [X] T024 [US1] Implement repeated-space, tab, and whitespace normalization in modules/text/cleanup.py
- [X] T025 [US1] Implement single-line-break collapse, paragraph preservation, and list-like break preservation in modules/text/cleanup.py
- [X] T026 [US1] Implement Arabic and English punctuation spacing normalization without punctuation removal in modules/text/cleanup.py
- [X] T027 [US1] Implement conservative garbage review with PRESERVED_UNCERTAIN_FRAGMENT and NOISY_TEXT warnings in modules/text/cleanup.py
- [X] T028 [US1] Implement empty input status, guidance, and unknown language/direction defaults in modules/text/cleanup.py
- [X] T029 [US1] Implement cleanup idempotence safeguards in modules/text/cleanup.py
- [X] T030 [US1] Export clean_ocr_text API from modules/text/__init__.py
- [X] T031 [US1] Run User Story 1 validation with python -m pytest tests/unit/test_text_cleanup_models.py tests/unit/test_text_cleanup.py

**Checkpoint**: User Story 1 is independently complete and provides the Phase 5 MVP.

---

## Phase 4: User Story 2 - Preserve Arabic and Mixed Text Readability (Priority: P2)

**Goal**: Preserve Arabic, English, and mixed Arabic/English text readability while maintaining logical reading order and direction metadata for later reading and display workflows.

**Independent Test**: Provide Arabic-only, English-only, and mixed Arabic/English OCR samples; verify cleaned text remains readable, both language segments are preserved, and direction metadata is correct.

### Tests for User Story 2

- [X] T032 [P] [US2] Add failing RTL tests for Arabic logical-order preservation in tests/unit/test_rtl_fixer.py
- [X] T033 [P] [US2] Add failing RTL tests for mixed Arabic/English segment preservation in tests/unit/test_rtl_fixer.py
- [X] T034 [P] [US2] Add failing cleanup tests for Arabic readability with spacing noise and punctuation in tests/unit/test_text_cleanup.py
- [X] T035 [P] [US2] Add failing cleanup tests for English readability with OCR spacing noise in tests/unit/test_text_cleanup.py
- [X] T036 [P] [US2] Add failing cleanup tests for mixed numbers, dates, prices, and symbols preserving meaningful tokens in tests/unit/test_text_cleanup.py
- [X] T037 [P] [US2] Add failing cleanup tests for Arabic diacritics and Arabic punctuation preservation in tests/unit/test_text_cleanup.py

### Implementation for User Story 2

- [X] T038 [US2] Implement detect_text_direction for RTL, LTR, mixed, and unknown direction in modules/text/rtl_fixer.py
- [X] T039 [US2] Implement preserve_logical_order helper that avoids display-only reversal in modules/text/rtl_fixer.py
- [X] T040 [US2] Integrate direction detection into TextCleanupResult construction in modules/text/cleanup.py
- [X] T041 [US2] Refine cleanup rules to preserve Arabic diacritics and Arabic punctuation in modules/text/cleanup.py
- [X] T042 [US2] Refine cleanup rules to preserve mixed numbers, dates, prices, and symbols in modules/text/cleanup.py
- [X] T043 [US2] Add MIXED_DIRECTION warnings when RTL and LTR evidence coexist in modules/text/cleanup.py
- [X] T044 [US2] Export RTL helpers from modules/text/__init__.py
- [X] T045 [US2] Run User Story 2 validation with python -m pytest tests/unit/test_rtl_fixer.py tests/unit/test_text_cleanup.py

**Checkpoint**: User Stories 1 and 2 are independently complete; Arabic and mixed text remain readable after cleanup.

---

## Phase 5: User Story 3 - Identify Text Language for Later Workflows (Priority: P3)

**Goal**: Classify cleaned text as Arabic, English, mixed, or unknown using deterministic evidence thresholds and expose confidence/evidence details for later TTS and translation routing.

**Independent Test**: Provide Arabic, English, mixed, empty, very short, and symbol-heavy samples; verify stable language, confidence, evidence counts, direction, and unknown results when evidence is insufficient.

### Tests for User Story 3

- [X] T046 [P] [US3] Add failing language tests for Arabic-only, English-only, and mixed-language classification in tests/unit/test_language_detector.py
- [X] T047 [P] [US3] Add failing language tests for 60 percent dominant-language evidence threshold in tests/unit/test_language_detector.py
- [X] T048 [P] [US3] Add failing language tests for empty, very short, symbol-heavy, and insufficient-evidence unknown results in tests/unit/test_language_detector.py
- [X] T049 [P] [US3] Add failing language tests for confidence, evidence counts, dominant ratio, warnings, and direction in tests/unit/test_language_detector.py
- [X] T050 [P] [US3] Add failing cleanup integration tests for language detection results in TextCleanupResult in tests/unit/test_text_cleanup.py

### Implementation for User Story 3

- [X] T051 [US3] Implement detect_language with Arabic and English character evidence counts in modules/text/language_detector.py
- [X] T052 [US3] Implement 60 percent dominant-language threshold and meaningful mixed-language evidence rules in modules/text/language_detector.py
- [X] T053 [US3] Implement unknown classification for empty, symbol-heavy, very short, and insufficient-evidence text in modules/text/language_detector.py
- [X] T054 [US3] Implement confidence, dominant_ratio, warning, and direction population in modules/text/language_detector.py
- [X] T055 [US3] Integrate detect_language into clean_ocr_text result building in modules/text/cleanup.py
- [X] T056 [US3] Export detect_language and LanguageDetectionResult APIs from modules/text/__init__.py
- [X] T057 [US3] Run User Story 3 validation with python -m pytest tests/unit/test_language_detector.py tests/unit/test_text_cleanup.py

**Checkpoint**: All user stories are independently functional and Phase 5 can provide clean text plus language/direction metadata for later workflows.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate privacy, scope boundaries, documentation, and full Phase 5 quality gates.

- [X] T058 [P] Add failing privacy tests for safe metadata excluding raw_text, clean_text, snippets, secrets, and debug paths in tests/unit/test_text_logging_privacy.py
- [X] T059 [P] Add failing privacy tests for text appearing in logs only when debug mode and sensitive-text logging are both enabled in tests/unit/test_text_logging_privacy.py
- [X] T060 Implement text_log_metadata and should_include_text_in_logs privacy helpers in modules/text/cleanup.py
- [X] T061 [P] Add Phase 5 scope-boundary tests preventing OCR, camera, image processing, translation, voice, TTS, and assistant workflow calls in tests/unit/test_text_scope_boundaries.py
- [X] T062 [P] Update docs/architecture.md with Phase 5 cleanup, RTL handling, language detection, privacy, and scope boundaries
- [X] T063 [P] Update docs/troubleshooting.md with empty text, noisy text, uncertain language, mixed direction, and sensitive logging guidance
- [X] T064 [P] Update quickstart validation notes in specs/006-phase5-text-cleanup/quickstart.md with actual test commands and expected local-only behavior
- [X] T065 Run full Phase 5 unit validation with python -m pytest tests/unit
- [X] T066 Run optional quality validation with python -m ruff check .
- [X] T067 Run optional formatter/type checks when installed with python -m black --check . and python -m mypy .
- [X] T068 Mark completed tasks in specs/006-phase5-text-cleanup/tasks.md after each task is implemented and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can reuse US1 cleanup entry point but remains independently testable through RTL and mixed-text fixtures.
- **User Story 3 (Phase 5)**: Depends on Foundational; integrates with US1 result building after language detection is implemented.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **US1 Read Clean OCR Text Aloud**: No dependency on other stories after Foundational.
- **US2 Preserve Arabic and Mixed Text Readability**: Can start after Foundational, but final integration into `clean_ocr_text` is easiest after US1.
- **US3 Identify Text Language for Later Workflows**: Can start after Foundational, but final integration into `TextCleanupResult` is easiest after US1.

### Parallel Opportunities

- Setup fixture tasks T004 and T005 can run in parallel.
- Foundational tests T007, T008, and T009 can be written in parallel.
- US1 test tasks T016 through T022 can be written in parallel.
- US2 test tasks T032 through T037 can be written in parallel.
- US3 test tasks T046 through T050 can be written in parallel.
- Polish documentation, privacy tests, and scope tests T058, T059, T061, T062, T063, and T064 can be worked on in parallel when implementation is stable.

---

## Parallel Example: User Story 1

```text
Task: "Add failing cleanup test for preserving raw_text exactly while producing clean_text in tests/unit/test_text_cleanup.py"
Task: "Add failing cleanup tests for repeated spaces, tabs, and simple whitespace normalization in tests/unit/test_text_cleanup.py"
Task: "Add failing cleanup tests for collapsing single OCR line breaks while preserving blank-line paragraphs in tests/unit/test_text_cleanup.py"
Task: "Add failing cleanup tests for Arabic and English punctuation spacing normalization in tests/unit/test_text_cleanup.py"
```

---

## Parallel Example: User Story 2

```text
Task: "Add failing RTL tests for Arabic logical-order preservation in tests/unit/test_rtl_fixer.py"
Task: "Add failing RTL tests for mixed Arabic/English segment preservation in tests/unit/test_rtl_fixer.py"
Task: "Add failing cleanup tests for mixed numbers, dates, prices, and symbols preserving meaningful tokens in tests/unit/test_text_cleanup.py"
```

---

## Parallel Example: User Story 3

```text
Task: "Add failing language tests for Arabic-only, English-only, and mixed-language classification in tests/unit/test_language_detector.py"
Task: "Add failing language tests for 60 percent dominant-language evidence threshold in tests/unit/test_language_detector.py"
Task: "Add failing language tests for empty, very short, symbol-heavy, and insufficient-evidence unknown results in tests/unit/test_language_detector.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational models and metadata helpers.
3. Complete Phase 3 User Story 1.
4. Stop and validate with `python -m pytest tests/unit/test_text_cleanup_models.py tests/unit/test_text_cleanup.py`.
5. Demo raw-text preservation and readable clean text with fixture samples.

### Incremental Delivery

1. Setup plus Foundational gives stable contracts.
2. US1 delivers clean text for later reading.
3. US2 adds Arabic and mixed-direction safety.
4. US3 adds language metadata for later TTS and translation routing.
5. Polish verifies privacy, scope boundaries, docs, and full unit validation.

### Quality Gates

- Tests for each story must be written before implementation and fail for missing behavior.
- Do not log raw OCR text or clean text by default.
- Do not import or call OCR execution, camera capture, image processing, translation, voice, TTS, or assistant orchestration from Phase 5 modules.
- Preserve raw OCR text exactly in all successful cleanup results.
- Keep cleanup deterministic and idempotent for fixture samples.
