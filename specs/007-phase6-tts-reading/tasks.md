# Tasks: Phase 6 TTS Reading Controller

**Input**: Design documents from `/specs/007-phase6-tts-reading/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tts-reading-contract.md, quickstart.md

**Tests**: Included because the constitution and feature specification require deterministic validation for TTS engine boundaries, Arabic/English reading, playback controls, repeat behavior, privacy-safe logging, and scope boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed earlier phases
- **[Story]**: User story label, such as [US1], [US2], or [US3]
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 6 module files, fixtures, and smoke-test script locations.

- [X] T001 Create Phase 6 placeholder modules in modules/voice/voice_models.py, modules/voice/tts_engine.py, modules/text/segmentation.py, and modules/assistant/reading_controller.py
- [X] T002 [P] Update module exports for Phase 6 public types in modules/voice/__init__.py, modules/text/__init__.py, and modules/assistant/__init__.py
- [X] T003 [P] Create deterministic segmentation fixture notes in tests/fixtures/text/segmentation_cases.md
- [X] T004 [P] Create eSpeak NG smoke-test script skeleton in scripts/test_tts.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared data contracts and utilities that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Write failing model tests for SpeechRequest, SpeechResult, TTSError, ReadingState, TextSegment, and ReadingControlCommand in tests/unit/test_tts_models.py
- [X] T006 Implement SpeechRequest, SpeechResult, TTSError, ReadingState, TextSegment, ReadingControlCommand, operation enums, error-code enums, and rate clamping helpers in modules/voice/voice_models.py
- [X] T007 [P] Write failing segmentation tests for blank-line paragraphs and Arabic/English sentence punctuation in tests/unit/test_text_segmentation.py
- [X] T008 Implement paragraph and sentence segmentation helpers with stable segment IDs in modules/text/segmentation.py
- [X] T009 [P] Write failing TTS engine boundary tests for mocked eSpeak NG success, unavailable binary, non-zero exit, timeout, stop idempotence, and safe metadata in tests/unit/test_tts_engine.py
- [X] T010 Implement TTSEngine protocol, MockTTSEngine test helper, and EspeakNGEngine subprocess adapter in modules/voice/tts_engine.py
- [X] T011 Ensure Phase 6 exports do not break existing imports by updating modules/voice/__init__.py and modules/text/__init__.py

**Checkpoint**: Foundation ready. Speech models, segmentation, and engine boundary can be tested without the reading controller.

---

## Phase 3: User Story 1 - Hear Clean OCR Text Read Aloud (Priority: P1) MVP

**Goal**: Read clean Arabic or English OCR text aloud through a mockable TTS engine, update reading state, and return user-safe guidance.

**Independent Test**: Provide clean Arabic and English text to the reading controller with a mocked speech engine; verify reading starts, the expected text is sent to speech, state is active, and empty text returns guidance without an engine call.

### Tests for User Story 1

- [X] T012 [P] [US1] Write failing controller tests for Arabic reading, English reading, mixed text logical order, active state, and empty text in tests/unit/test_reading_controller.py
- [X] T013 [P] [US1] Write failing privacy tests proving start-reading logs exclude raw text, clean text, spoken text, and snippets in tests/unit/test_tts_logging_privacy.py
- [X] T014 [P] [US1] Write failing scope-boundary tests proving start-reading does not import or call camera, OCR, cleanup, translation, STT, command parser, or dialogue orchestration modules in tests/unit/test_tts_scope_boundaries.py

### Implementation for User Story 1

- [X] T015 [US1] Implement ReadingController constructor, state initialization, get_state, and safe result helpers in modules/assistant/reading_controller.py
- [X] T016 [US1] Implement start_reading for clean Arabic, English, and mixed text with no cleanup or OCR calls in modules/assistant/reading_controller.py
- [X] T017 [US1] Implement empty and whitespace-only text handling with no engine speak call in modules/assistant/reading_controller.py
- [X] T018 [US1] Update safe metadata and guidance handling for read-all success, no-readable-text, and engine failure in modules/assistant/reading_controller.py
- [X] T019 [US1] Document the Phase 6 read-aloud path and privacy expectations in docs/architecture.md
- [X] T020 [US1] Run focused US1 validation with python -m pytest tests/unit/test_tts_models.py tests/unit/test_tts_engine.py tests/unit/test_text_segmentation.py tests/unit/test_reading_controller.py tests/unit/test_tts_logging_privacy.py tests/unit/test_tts_scope_boundaries.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Control Playback Without Visual Feedback (Priority: P2)

**Goal**: Allow stop, pause, continue, and rate changes with state updates and spoken guidance that do not require visual confirmation.

**Independent Test**: Use a mocked speech engine and active reading state; verify stop, native pause, pause fallback, continue, continue fallback, and rate clamping update state and return guidance.

### Tests for User Story 2

- [X] T021 [P] [US2] Write failing controller tests for stop active, stop inactive, native pause, native continue, pause fallback, and continue replay fallback in tests/unit/test_reading_controller.py
- [X] T022 [P] [US2] Write failing controller tests for default 150 words-per-minute rate and clamping requested rates to 80-220 in tests/unit/test_reading_controller.py
- [X] T023 [P] [US2] Write failing engine tests for unsupported pause/resume results and controller-owned fallback metadata in tests/unit/test_tts_engine.py

### Implementation for User Story 2

- [X] T024 [US2] Implement stop control with idempotent inactive-state behavior in modules/assistant/reading_controller.py
- [X] T025 [US2] Implement pause control using native pause when supported and stop-and-preserve-current-segment fallback when unsupported in modules/assistant/reading_controller.py
- [X] T026 [US2] Implement continue_reading using native resume when supported and current-segment replay when native resume is unavailable in modules/assistant/reading_controller.py
- [X] T027 [US2] Implement set_rate and future-request rate application with 80-220 clamping in modules/assistant/reading_controller.py
- [X] T028 [US2] Extend EspeakNGEngine pause/resume unsupported behavior and stop result mapping in modules/voice/tts_engine.py
- [X] T029 [US2] Update troubleshooting notes for missing eSpeak NG, unsupported pause/resume fallback, and safe stop behavior in docs/troubleshooting.md
- [X] T030 [US2] Run focused US2 validation with python -m pytest tests/unit/test_reading_controller.py tests/unit/test_tts_engine.py

**Checkpoint**: User Stories 1 and 2 work independently and together.

---

## Phase 5: User Story 3 - Repeat Recent Text Segments (Priority: P3)

**Goal**: Track last successfully requested sentence and paragraph and repeat only the requested segment when history exists.

**Independent Test**: Provide segmented clean text with several sentences and paragraphs; verify repeat last sentence and repeat last paragraph speak only the tracked segment, and repeat without history returns guidance without unrelated speech.

### Tests for User Story 3

- [X] T031 [P] [US3] Write failing segmentation fixture tests for Arabic, English, and mixed sentence and paragraph samples in tests/unit/test_text_segmentation.py
- [X] T032 [P] [US3] Write failing controller tests for last sentence history, last paragraph history, repeat sentence, repeat paragraph, no-history guidance, and no unrelated speech in tests/unit/test_reading_controller.py
- [X] T033 [P] [US3] Write failing controller tests proving TTS failures leave reading inactive and preserve prior successful repeat history in tests/unit/test_reading_controller.py

### Implementation for User Story 3

- [X] T034 [US3] Extend segmentation fixtures for repeat behavior coverage in tests/fixtures/text/segmentation_cases.md
- [X] T035 [US3] Track current segment, last successfully requested sentence, and last successfully requested paragraph during start, continue, and repeat operations in modules/assistant/reading_controller.py
- [X] T036 [US3] Implement repeat_last_sentence with no-history guidance and single-segment speech request in modules/assistant/reading_controller.py
- [X] T037 [US3] Implement repeat_last_paragraph with no-history guidance and single-segment speech request in modules/assistant/reading_controller.py
- [X] T038 [US3] Implement TTS failure state handling that leaves reading inactive and preserves prior successful repeat history in modules/assistant/reading_controller.py
- [X] T039 [US3] Run focused US3 validation with python -m pytest tests/unit/test_text_segmentation.py tests/unit/test_reading_controller.py

**Checkpoint**: All Phase 6 user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, script completion, documentation, and regression checks across Phase 6.

- [X] T040 [P] Write failing script tests for scripts/test_tts.py argument parsing, structured success, structured unavailable-engine failure, and no text leakage in tests/unit/test_tts_script.py
- [X] T041 Implement scripts/test_tts.py live eSpeak NG smoke-test behavior with safe structured output and no default text logging
- [X] T042 [P] Update specs/007-phase6-tts-reading/quickstart.md with final validation commands and any environment notes discovered during implementation
- [X] T043 [P] Update docs/architecture.md with final Phase 6 module boundaries and reading-state behavior
- [X] T044 [P] Update docs/troubleshooting.md with final TTS error categories and recovery guidance
- [X] T045 Run full unit regression with python -m pytest tests/unit
- [X] T046 Run lint validation with python -m ruff check .
- [X] T047 Run optional formatting/type validation with python -m black --check . and python -m mypy . when installed
- [X] T048 Verify Phase 6 scope, privacy, and no-placeholder completion against specs/007-phase6-tts-reading/quickstart.md
- [X] T049 Mark all completed tasks in specs/007-phase6-tts-reading/tasks.md after validation succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational; can be developed independently with a mocked active state but should validate with US1 behavior
- **User Story 3 (Phase 5)**: Depends on Foundational; can be developed independently with fixtures but integrates naturally after US1 state exists
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: No hard dependency on US1 implementation if tests build active state directly, but final validation should include US1 start-reading flow
- **US3 (P3)**: Requires segmentation and ReadingState from Foundational; final validation should include US1 read-start history

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Implement models and shared helpers before controller behavior
- Implement controller behavior before documentation and focused validation
- Validate each story before starting the next priority phase

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001
- T007 and T009 can run in parallel after model expectations in T005 are known
- US1 tests T012, T013, and T014 can run in parallel
- US2 tests T021, T022, and T023 can run in parallel
- US3 tests T031, T032, and T033 can run in parallel
- Polish documentation tasks T042, T043, and T044 can run in parallel after implementation stabilizes

---

## Parallel Example: User Story 1

```text
Task: "Write failing controller tests for Arabic reading, English reading, mixed text logical order, active state, and empty text in tests/unit/test_reading_controller.py"
Task: "Write failing privacy tests proving start-reading logs exclude raw text, clean text, spoken text, and snippets in tests/unit/test_tts_logging_privacy.py"
Task: "Write failing scope-boundary tests proving start-reading does not import or call camera, OCR, cleanup, translation, STT, command parser, or dialogue orchestration modules in tests/unit/test_tts_scope_boundaries.py"
```

## Parallel Example: User Story 2

```text
Task: "Write failing controller tests for stop active, stop inactive, native pause, native continue, pause fallback, and continue replay fallback in tests/unit/test_reading_controller.py"
Task: "Write failing controller tests for default 150 words-per-minute rate and clamping requested rates to 80-220 in tests/unit/test_reading_controller.py"
Task: "Write failing engine tests for unsupported pause/resume results and controller-owned fallback metadata in tests/unit/test_tts_engine.py"
```

## Parallel Example: User Story 3

```text
Task: "Write failing segmentation fixture tests for Arabic, English, and mixed sentence and paragraph samples in tests/unit/test_text_segmentation.py"
Task: "Write failing controller tests for last sentence history, last paragraph history, repeat sentence, repeat paragraph, no-history guidance, and no unrelated speech in tests/unit/test_reading_controller.py"
Task: "Write failing controller tests proving TTS failures leave reading inactive and preserve prior successful repeat history in tests/unit/test_reading_controller.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation for models, segmentation, and TTS engine boundary.
3. Complete Phase 3 US1 read-aloud behavior.
4. Stop and validate US1 independently with mocked Arabic, English, mixed, and empty-text cases.

### Incremental Delivery

1. Deliver US1 so clean OCR text can be read aloud.
2. Add US2 playback controls and rate management without breaking read-aloud behavior.
3. Add US3 repeat sentence and repeat paragraph behavior using tracked segment history.
4. Complete script, documentation, privacy, scope, lint, and regression checks.

### Quality Gates

- No task may introduce paid TTS, cloud-only speech, OCR execution, camera capture, text cleanup, translation, STT, command parsing, or full workflow orchestration into Phase 6.
- Default logs must never include raw OCR text, clean text, spoken text, sentence snippets, or paragraph snippets.
- TTS engine failures must return structured results and leave reading inactive.
- Unsupported native pause/resume must use the documented stop-and-replay fallback.
