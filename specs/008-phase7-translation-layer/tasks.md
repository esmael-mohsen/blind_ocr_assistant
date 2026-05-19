# Tasks: Phase 7 Translation Layer

**Input**: Design documents from `/specs/008-phase7-translation-layer/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/translation-contract.md, quickstart.md

**Tests**: Included because the constitution and feature specification require deterministic validation for Arabic/English translation, online-first/offline-fallback routing, translated-result validation, reading handoff, privacy-safe logging, latest-only state, and scope boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed earlier phases
- **[Story]**: User story label, such as [US1], [US2], or [US3]
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 7 module files, fixtures, and public package exports.

- [X] T001 Create Phase 7 placeholder modules in modules/translation/base.py, modules/translation/translation_models.py, modules/translation/libre_translate_client.py, modules/translation/argos_fallback.py, and modules/assistant/translation_controller.py
- [X] T002 [P] Update Phase 7 public exports in modules/translation/__init__.py and modules/assistant/__init__.py
- [X] T003 [P] Create deterministic translation fixture notes in tests/fixtures/text/translation_cases.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared data contracts, provider boundaries, and validation helpers that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Write failing model tests for TranslationRequest, TranslationResult, TranslationEngine metadata, TranslationError, TranslationState, and TranslationControlRequest in tests/unit/test_translation_models.py
- [X] T005 Implement TranslationRequest, TranslationResult, TranslationError, TranslationState, TranslationControlRequest, path enums, language enums, operation enums, and error-code enums in modules/translation/translation_models.py
- [X] T006 [P] Write failing safe-metadata tests proving translation models exclude raw OCR text, clean text, translated text, source snippets, and translated snippets in tests/unit/test_translation_models.py
- [X] T007 Implement privacy-safe metadata helpers, text length fields, and stable guidance defaults in modules/translation/translation_models.py
- [X] T008 [P] Write failing translation engine boundary tests for supported directions, unavailable providers, provider exceptions, structured failures, and safe metadata in tests/unit/test_translation_base.py
- [X] T009 Implement TranslationEngine protocol, MockTranslationEngine test helper, direction validation, provider exception mapping, and result-validation helpers in modules/translation/base.py
- [X] T010 [P] Write failing validation tests for empty output, wrong-language output, unchanged non-no-op output, valid Arabic output, valid English output, and same-language no-op allowance in tests/unit/test_translation_base.py
- [X] T011 Ensure foundational Phase 7 imports remain stable by updating modules/translation/__init__.py and modules/assistant/__init__.py

**Checkpoint**: Foundation ready. Translation models, safe metadata, provider boundaries, and translated-result validation can be tested without the controller.

---

## Phase 3: User Story 1 - Hear Latest Clean Text Translated (Priority: P1) MVP

**Goal**: Translate clean Arabic or English OCR text, return a structured translated result, update latest-only state, and hand successful output to the reading layer when available.

**Independent Test**: Provide clean Arabic text with target English and clean English text with target Arabic using mocked providers; verify success metadata, source and target languages, reading handoff, no-text guidance, and provider call behavior.

### Tests for User Story 1

- [X] T012 [P] [US1] Write failing controller tests for Arabic-to-English success, English-to-Arabic success, reading-layer available handoff, reading-layer unavailable guidance, and empty text in tests/unit/test_translation_controller.py
- [X] T013 [P] [US1] Write failing controller tests proving empty and whitespace-only text do not call online or offline translation engines in tests/unit/test_translation_controller.py
- [X] T014 [P] [US1] Write failing latest-state tests proving successful translation replaces previous source and translated text in tests/unit/test_translation_controller.py
- [X] T015 [P] [US1] Write failing privacy tests proving successful translation logs exclude raw OCR text, clean text, translated text, and snippets in tests/unit/test_translation_logging_privacy.py

### Implementation for User Story 1

- [X] T016 [US1] Implement TranslationController constructor, reading boundary injection, engine injection, state initialization, and get_state in modules/assistant/translation_controller.py
- [X] T017 [US1] Implement translate_latest request construction, language normalization, empty-text guidance, and no-provider-call behavior in modules/assistant/translation_controller.py
- [X] T018 [US1] Implement direct Arabic-to-English and English-to-Arabic translation success routing with a mocked online engine in modules/assistant/translation_controller.py
- [X] T019 [US1] Implement reading handoff for successful translated results and reading-unavailable guidance in modules/assistant/translation_controller.py
- [X] T020 [US1] Implement latest-only TranslationState replacement for successful translations in modules/assistant/translation_controller.py
- [X] T021 [US1] Document the Phase 7 MVP translation and reading handoff path in docs/architecture.md
- [X] T022 [US1] Run focused US1 validation with python -m pytest tests/unit/test_translation_models.py tests/unit/test_translation_base.py tests/unit/test_translation_controller.py tests/unit/test_translation_logging_privacy.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Continue When Online Translation Is Unavailable (Priority: P2)

**Goal**: Route translation through a free online provider first when allowed, then local offline fallback when online is disabled, unavailable, times out, fails, or returns an invalid result.

**Independent Test**: Simulate online disabled, unavailable, timeout, failure, invalid response, and all-provider failure; verify fallback use, local success, structured final failure, and user-safe recovery guidance.

### Tests for User Story 2

- [X] T023 [P] [US2] Write failing LibreTranslate client tests for allow_online false, HTTP success, service unavailable, timeout, invalid JSON, empty translated text, and safe metadata in tests/unit/test_libre_translate_client.py
- [X] T024 [P] [US2] Write failing Argos fallback tests for lazy import, missing package, missing model, translation success, translation failure, and safe metadata in tests/unit/test_argos_fallback.py
- [X] T025 [P] [US2] Write failing controller fallback tests for online disabled, unavailable, timeout, failure, invalid online result, offline success, offline disallowed, and all-provider failure in tests/unit/test_translation_controller.py
- [X] T026 [P] [US2] Extend privacy tests proving fallback and all-provider-failure logs exclude raw OCR text, clean text, translated text, and snippets in tests/unit/test_translation_logging_privacy.py

### Implementation for User Story 2

- [X] T027 [US2] Implement LibreTranslateClient constructor, request payload mapping, timeout handling, HTTP response parsing, and structured failure mapping in modules/translation/libre_translate_client.py
- [X] T028 [US2] Implement LibreTranslateClient safe metadata and allow_online false behavior without sending text in modules/translation/libre_translate_client.py
- [X] T029 [US2] Implement ArgosTranslateFallback lazy package loading, installed-language lookup, local translation success, unavailable-resource failure, and exception mapping in modules/translation/argos_fallback.py
- [X] T030 [US2] Implement online-first routing, offline fallback eligibility, fallback_used metadata, and invalid-result fallback in modules/assistant/translation_controller.py
- [X] T031 [US2] Implement all-provider-failure aggregation with stable TranslationError codes and recovery guidance in modules/assistant/translation_controller.py
- [X] T032 [US2] Update troubleshooting notes for online translation unavailable, local fallback unavailable, timeout, invalid result, and all-provider failure in docs/troubleshooting.md
- [X] T033 [US2] Run focused US2 validation with python -m pytest tests/unit/test_libre_translate_client.py tests/unit/test_argos_fallback.py tests/unit/test_translation_controller.py tests/unit/test_translation_logging_privacy.py

**Checkpoint**: User Stories 1 and 2 work independently and together.

---

## Phase 5: User Story 3 - Translate With Clear Language Direction And Privacy (Priority: P3)

**Goal**: Enforce supported Arabic/English directions, require explicit source language for mixed or unknown input, treat same-language requests as successful no-op results, and protect sensitive text from default logs.

**Independent Test**: Provide Arabic, English, mixed, unknown, unsupported, and same-language requests; verify direction handling, guidance, no provider calls where required, privacy-safe metadata, latest-only state, and Phase 7 scope boundaries.

### Tests for User Story 3

- [X] T034 [P] [US3] Write failing direction tests for known Arabic to English, known English to Arabic, unsupported source, unsupported target, mixed without explicit source, unknown without explicit source, and explicit supported source in tests/unit/test_translation_controller.py
- [X] T035 [P] [US3] Write failing same-language no-op tests proving providers are not called, clean text is preserved for reading, result path is no_op, and guidance says translation was not needed in tests/unit/test_translation_controller.py
- [X] T036 [P] [US3] Write failing privacy tests proving safe metadata and logs exclude text content across success, fallback, no-op, direction-required, unsupported-language, and failure results in tests/unit/test_translation_logging_privacy.py
- [X] T037 [P] [US3] Write failing scope-boundary tests proving Phase 7 code does not import or call camera capture, OCR cascade, image processing, text cleanup, voice command parsing, or full dialogue orchestration in tests/unit/test_translation_scope_boundaries.py
- [X] T038 [P] [US3] Extend translation fixture notes for Arabic, English, mixed, unknown, unsupported, same-language, invalid-result, and fallback samples in tests/fixtures/text/translation_cases.md

### Implementation for User Story 3

- [X] T039 [US3] Implement supported-language and target-language validation with user-safe guidance in modules/assistant/translation_controller.py
- [X] T040 [US3] Implement mixed and unknown source-language handling that requires explicit Arabic or English source before providers are called in modules/assistant/translation_controller.py
- [X] T041 [US3] Implement same-language successful no-op results with preserved clean text, no provider calls, optional reading handoff, and latest-only state replacement in modules/assistant/translation_controller.py
- [X] T042 [US3] Harden privacy-safe logging and safe metadata for controller, online provider, offline provider, no-op path, and failure paths in modules/translation/translation_models.py, modules/translation/base.py, modules/translation/libre_translate_client.py, modules/translation/argos_fallback.py, and modules/assistant/translation_controller.py
- [X] T043 [US3] Verify and document Phase 7 scope boundaries in docs/architecture.md
- [X] T044 [US3] Run focused US3 validation with python -m pytest tests/unit/test_translation_controller.py tests/unit/test_translation_logging_privacy.py tests/unit/test_translation_scope_boundaries.py

**Checkpoint**: All Phase 7 user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, quickstart alignment, and regression checks across Phase 7.

- [X] T045 [P] Update specs/008-phase7-translation-layer/quickstart.md with final validation commands and any environment notes discovered during implementation
- [X] T046 [P] Update docs/architecture.md with final Phase 7 translation module boundaries, provider routing, latest-only state, and reading handoff behavior
- [X] T047 [P] Update docs/troubleshooting.md with final Phase 7 error categories, recovery guidance, and optional online/offline dependency notes
- [X] T048 Run focused Phase 7 validation with python -m pytest tests/unit/test_translation_models.py tests/unit/test_translation_base.py tests/unit/test_libre_translate_client.py tests/unit/test_argos_fallback.py tests/unit/test_translation_controller.py tests/unit/test_translation_logging_privacy.py tests/unit/test_translation_scope_boundaries.py
- [X] T049 Run full unit regression with python -m pytest tests/unit
- [X] T050 Run lint validation with python -m ruff check .
- [X] T051 Run optional formatting/type validation with python -m black --check . and python -m mypy . when installed
- [X] T052 Verify Phase 7 scope, privacy, fallback, latest-only state, and no-placeholder completion against specs/008-phase7-translation-layer/quickstart.md
- [X] T053 Mark all completed tasks in specs/008-phase7-translation-layer/tasks.md after validation succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational; can be developed independently with mocked providers but should validate with US1 success behavior
- **User Story 3 (Phase 5)**: Depends on Foundational; can be developed independently with mocked providers but naturally hardens US1 and US2 controller behavior
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: No hard dependency on US1 implementation if tests call the controller with mocked providers, but final validation should include US1 success routing
- **US3 (P3)**: No hard dependency on US2 provider implementation if tests use mocked providers, but final validation should include online, offline, no-op, and failure paths

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Implement models and shared helpers before provider or controller behavior
- Implement provider boundaries before fallback orchestration
- Implement controller behavior before documentation and focused validation
- Validate each story before starting the next priority phase

### Parallel Opportunities

- T002 and T003 can run in parallel after T001
- T006, T008, and T010 can run in parallel after T004 establishes model expectations
- US1 tests T012, T013, T014, and T015 can run in parallel
- US2 tests T023, T024, T025, and T026 can run in parallel
- US3 tests T034, T035, T036, T037, and T038 can run in parallel
- Polish documentation tasks T045, T046, and T047 can run in parallel after implementation stabilizes

---

## Parallel Example: User Story 1

```text
Task: "Write failing controller tests for Arabic-to-English success, English-to-Arabic success, reading-layer available handoff, reading-layer unavailable guidance, and empty text in tests/unit/test_translation_controller.py"
Task: "Write failing controller tests proving empty and whitespace-only text do not call online or offline translation engines in tests/unit/test_translation_controller.py"
Task: "Write failing latest-state tests proving successful translation replaces previous source and translated text in tests/unit/test_translation_controller.py"
Task: "Write failing privacy tests proving successful translation logs exclude raw OCR text, clean text, translated text, and snippets in tests/unit/test_translation_logging_privacy.py"
```

## Parallel Example: User Story 2

```text
Task: "Write failing LibreTranslate client tests for allow_online false, HTTP success, service unavailable, timeout, invalid JSON, empty translated text, and safe metadata in tests/unit/test_libre_translate_client.py"
Task: "Write failing Argos fallback tests for lazy import, missing package, missing model, translation success, translation failure, and safe metadata in tests/unit/test_argos_fallback.py"
Task: "Write failing controller fallback tests for online disabled, unavailable, timeout, failure, invalid online result, offline success, offline disallowed, and all-provider failure in tests/unit/test_translation_controller.py"
Task: "Extend privacy tests proving fallback and all-provider-failure logs exclude raw OCR text, clean text, translated text, and snippets in tests/unit/test_translation_logging_privacy.py"
```

## Parallel Example: User Story 3

```text
Task: "Write failing direction tests for known Arabic to English, known English to Arabic, unsupported source, unsupported target, mixed without explicit source, unknown without explicit source, and explicit supported source in tests/unit/test_translation_controller.py"
Task: "Write failing same-language no-op tests proving providers are not called, clean text is preserved for reading, result path is no_op, and guidance says translation was not needed in tests/unit/test_translation_controller.py"
Task: "Write failing privacy tests proving safe metadata and logs exclude text content across success, fallback, no-op, direction-required, unsupported-language, and failure results in tests/unit/test_translation_logging_privacy.py"
Task: "Write failing scope-boundary tests proving Phase 7 code does not import or call camera capture, OCR cascade, image processing, text cleanup, voice command parsing, or full dialogue orchestration in tests/unit/test_translation_scope_boundaries.py"
Task: "Extend translation fixture notes for Arabic, English, mixed, unknown, unsupported, same-language, invalid-result, and fallback samples in tests/fixtures/text/translation_cases.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation for translation models, engine boundaries, safe metadata, and validation helpers.
3. Complete Phase 3 US1 translation and reading handoff behavior.
4. Stop and validate US1 independently with mocked Arabic-to-English, English-to-Arabic, reading available, reading unavailable, and empty-text cases.

### Incremental Delivery

1. Deliver US1 so latest clean OCR text can be translated and read.
2. Add US2 online-first/offline-fallback routing without breaking direct translation behavior.
3. Add US3 direction safety, same-language no-op handling, latest-only state checks, privacy hardening, and scope boundaries.
4. Complete documentation, quickstart, lint, optional formatting/type checks, and full unit regression.

### Quality Gates

- No task may introduce paid translation, cloud-only translation, camera capture, OCR execution, image processing, text cleanup, voice command parsing, or full assistant orchestration into Phase 7.
- Default logs and safe metadata must never include raw OCR text, clean text, translated text, source snippets, translated snippets, provider secrets, or endpoint credentials.
- Online provider failures, invalid results, unavailable offline resources, and reading handoff failures must return structured results without uncaught provider exceptions.
- Offline translation packages or models must be lazy-loaded and absent dependencies must produce structured unavailable results.
- Normal translation state must keep only the latest source and translated result, replacing earlier successful state on each new successful request.
