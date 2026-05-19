# Tasks: Phase 9 Full Assistive Workflow Integration

**Input**: Design documents from `/specs/010-phase9-workflow-integration/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/workflow-integration-contract.md, quickstart.md

**Tests**: Included because the constitution and feature specification require deterministic validation for full read workflow integration, latest-state lifecycle, spoken guidance, recoverable failures, privacy-safe logging, shutdown, and scope boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed earlier phases
- **[Story]**: User story label, such as [US1], [US2], [US3], or [US4]
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 9 orchestration modules, entrypoint boundaries, and test files without changing existing engine behavior.

- [X] T001 Create Phase 9 orchestration placeholders in modules/assistant/state.py, modules/assistant/workflow.py, tests/unit/test_assistant_state.py, tests/unit/test_assistant_workflow.py, tests/unit/test_assistant_workflow_failures.py, tests/unit/test_assistant_workflow_logging_privacy.py, tests/unit/test_assistant_workflow_scope_boundaries.py, tests/unit/test_main_assistant_entrypoint.py, tests/integration/test_full_read_workflow.py, and tests/integration/test_full_translate_workflow.py
- [X] T002 [P] Update Phase 9 public exports in modules/assistant/__init__.py
- [X] T003 [P] Update main.py to preserve the existing help/entrypoint behavior while reserving wiring points for the Phase 9 workflow
- [X] T004 [P] Add Phase 9 manual acceptance notes to specs/010-phase9-workflow-integration/quickstart.md if any environment-specific assumptions are discovered

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define assistant state, workflow result contracts, privacy-safe metadata, dependency injection boundaries, and operational lifecycle primitives that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Write failing assistant state tests for AssistantSession, AssistantState, WorkflowRequest, ReadWorkflowResult, TranslationWorkflowResult, SpokenStatus, WorkflowFailure, state replacement, and shutdown clearing in tests/unit/test_assistant_state.py
- [X] T006 Implement AssistantSession, AssistantState, WorkflowRequest, ReadWorkflowResult, TranslationWorkflowResult, SpokenStatus, WorkflowFailure, workflow mode enums, status enums, and error-code enums in modules/assistant/state.py
- [X] T007 [P] Write failing safe-metadata tests proving Phase 9 state and workflow results exclude images, depth maps, raw OCR text, clean text, translated text, command transcripts, speech input, snippets, tokens, secrets, and debug paths in tests/unit/test_assistant_state.py
- [X] T008 Implement privacy-safe metadata helpers, result update helpers, latest-success state helpers, and spoken guidance defaults in modules/assistant/state.py
- [X] T009 [P] Write failing workflow constructor tests for injected command, camera, OCR, cleanup, reading, translation, online-status, clock, and logger boundaries in tests/unit/test_assistant_workflow.py
- [X] T010 Implement AssistantWorkflow constructor, dependency injection fields, default state initialization, get_state, and safe status helpers in modules/assistant/workflow.py
- [X] T011 [P] Write failing boundary-wrapper tests for structured handling of boundary exceptions, TimeoutError, missing dependencies, and KeyboardInterrupt pass-through expectations in tests/unit/test_assistant_workflow_failures.py
- [X] T012 Implement boundary wrapper helpers that convert camera, OCR, cleanup, translation, TTS, command, timeout, and unexpected failures into WorkflowFailure-backed results in modules/assistant/workflow.py
- [X] T013 [P] Write failing operational lifecycle tests for shutdown_requested state, workflow_active guard, active-speech settlement hooks, and resource cleanup hooks in tests/unit/test_assistant_workflow.py
- [X] T014 Implement workflow_active guard, shutdown_requested guard, operational shutdown state transitions, and resource cleanup hook structure in modules/assistant/workflow.py
- [X] T015 Update modules/assistant/__init__.py with AssistantWorkflow and Phase 9 state exports after modules/assistant/state.py and modules/assistant/workflow.py are implemented

**Checkpoint**: Foundation ready. Assistant state, workflow result contracts, safe metadata, injected boundaries, and lifecycle guards can be tested without running hardware or live engines.

---

## Phase 3: User Story 1 - Complete Read Workflow By Voice (Priority: P1) MVP

**Goal**: Recognize a supported Arabic or English read command and complete capture, best-frame selection, OCR cascade, cleanup, latest-state update, and reading handoff in order.

**Independent Test**: Use mocked command, camera, OCR, cleanup, and reading boundaries; issue Arabic and English read commands; verify spoken status, ordered handoffs, latest clean text storage, selected OCR metadata, fallback metadata, and reading handoff without visual confirmation.

### Tests for User Story 1

- [X] T016 [P] [US1] Write failing unit tests for successful Arabic read command workflow ordering in tests/unit/test_assistant_workflow.py
- [X] T017 [P] [US1] Write failing unit tests for successful English read command workflow ordering in tests/unit/test_assistant_workflow.py
- [X] T018 [P] [US1] Write failing unit tests for OCR fallback metadata, selected OCR engine storage, cleanup language storage, and spoken progress guidance in tests/unit/test_assistant_workflow.py
- [X] T019 [P] [US1] Write failing integration tests for a mocked full read workflow from command recognition through reading handoff in tests/integration/test_full_read_workflow.py
- [X] T020 [P] [US1] Write failing privacy tests proving successful read workflow logs and safe metadata exclude image payloads, raw OCR text, clean text, translated text, command transcripts, speech input, snippets, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py

### Implementation for User Story 1

- [X] T021 [US1] Implement handle_command read-intent routing from DialogueManager results to run_read_workflow in modules/assistant/workflow.py
- [X] T022 [US1] Implement run_read_workflow capture burst handoff and best-frame selection handling in modules/assistant/workflow.py
- [X] T023 [US1] Implement accepted-frame to OCRCascadeRequest mapping and OCR cascade handoff in modules/assistant/workflow.py
- [X] T024 [US1] Implement OCRResult to TextCleanupRequest mapping and cleanup handoff in modules/assistant/workflow.py
- [X] T025 [US1] Implement clean text handoff to ReadingController.start_reading with detected language in modules/assistant/workflow.py
- [X] T026 [US1] Implement latest successful read state updates for raw text, clean text, language, selected OCR engine, fallback use, workflow status, and last guidance in modules/assistant/workflow.py
- [X] T027 [US1] Implement spoken progress, fallback, cleanup-ready, and reading-start guidance aggregation in modules/assistant/workflow.py
- [X] T028 [US1] Wire thin main.py dependency construction to expose a Phase 9 assistant workflow factory without starting live hardware during import
- [X] T029 [US1] Run focused US1 validation with python -m pytest tests/unit/test_assistant_state.py tests/unit/test_assistant_workflow.py tests/integration/test_full_read_workflow.py tests/unit/test_assistant_workflow_logging_privacy.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Translate Latest Read Text By Voice (Priority: P2)

**Goal**: Route translate-to-Arabic and translate-to-English commands to existing translation behavior using latest successful clean text, then read successful translations aloud.

**Independent Test**: Seed latest clean text through a successful or simulated read workflow; issue translate-to-Arabic and translate-to-English commands; verify target language, translation handoff, translated-state update, reading handoff, missing-text guidance, and stale/raw text protection.

### Tests for User Story 2

- [X] T030 [P] [US2] Write failing unit tests for translate-to-English command using latest clean Arabic text in tests/unit/test_assistant_workflow.py
- [X] T031 [P] [US2] Write failing unit tests for translate-to-Arabic command using latest clean English text in tests/unit/test_assistant_workflow.py
- [X] T032 [P] [US2] Write failing tests for no-latest-clean-text translation guidance and no translation boundary call in tests/unit/test_assistant_workflow_failures.py
- [X] T033 [P] [US2] Write failing tests proving failed read attempts do not clear latest clean text before translation in tests/unit/test_assistant_workflow.py
- [X] T034 [P] [US2] Write failing integration tests for read-then-translate-to-English and read-then-translate-to-Arabic flows in tests/integration/test_full_translate_workflow.py
- [X] T035 [P] [US2] Extend privacy tests proving translation workflow logs and safe metadata exclude source clean text, translated text, snippets, command transcripts, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py

### Implementation for User Story 2

- [X] T036 [US2] Implement handle_command translation-intent routing to run_translation_workflow in modules/assistant/workflow.py
- [X] T037 [US2] Implement run_translation_workflow latest-clean-text validation and no-text guidance in modules/assistant/workflow.py
- [X] T038 [US2] Implement translation_controller.translate_latest handoff with latest clean text, latest language, target language, and online/offline permissions in modules/assistant/workflow.py
- [X] T039 [US2] Implement successful translation state update for latest translated text, workflow status, fallback use, and last guidance in modules/assistant/workflow.py
- [X] T040 [US2] Implement translation failure handling that preserves previous clean text and previous translated text in modules/assistant/workflow.py
- [X] T041 [US2] Ensure translated reading handoff status from TranslationController is reflected in TranslationWorkflowResult guidance in modules/assistant/workflow.py
- [X] T042 [US2] Run focused US2 validation with python -m pytest tests/unit/test_assistant_workflow.py tests/unit/test_assistant_workflow_failures.py tests/integration/test_full_translate_workflow.py tests/unit/test_assistant_workflow_logging_privacy.py

**Checkpoint**: User Stories 1 and 2 work independently and together.

---

## Phase 5: User Story 3 - Recover From Workflow Problems (Priority: P3)

**Goal**: Convert camera, quality, OCR, cleanup, translation, TTS, command, timeout, and unexpected failures into structured spoken recovery guidance while keeping the assistant responsive and preserving safe latest state.

**Independent Test**: Simulate each failure category with mocked boundaries; verify structured errors, spoken guidance, no uncaught exceptions, previous successful text preservation, no automatic capture loops, and continued command responsiveness.

### Tests for User Story 3

- [X] T043 [P] [US3] Write failing tests for camera open failure, capture timeout, no frame candidates, and camera release failure guidance in tests/unit/test_assistant_workflow_failures.py
- [X] T044 [P] [US3] Write failing tests for all frames rejected by best-frame selection, recapture guidance, and no automatic repeated capture loop in tests/unit/test_assistant_workflow_failures.py
- [X] T045 [P] [US3] Write failing tests for OCR unavailable, OCR timeout, all OCR engines failed, no text detected, and weak OCR result guidance in tests/unit/test_assistant_workflow_failures.py
- [X] T046 [P] [US3] Write failing tests for cleanup-empty text, uncertain cleanup result, TTS failure, translation failure, and command unavailable guidance in tests/unit/test_assistant_workflow_failures.py
- [X] T047 [P] [US3] Write failing tests for component TimeoutError, unexpected exception wrapping, and assistant responsiveness after recoverable failures in tests/unit/test_assistant_workflow_failures.py
- [X] T048 [P] [US3] Write failing state preservation tests proving failed read and translation attempts retain previous successful clean text and translated text in tests/unit/test_assistant_workflow.py

### Implementation for User Story 3

- [X] T049 [US3] Implement camera and capture failure mapping to WorkflowFailure codes and spoken recovery guidance in modules/assistant/workflow.py
- [X] T050 [US3] Implement no-acceptable-frame handling that ends the read attempt, records recapture guidance, and performs no automatic capture loop in modules/assistant/workflow.py
- [X] T051 [US3] Implement OCR cascade failure and weak/no-text result mapping to WorkflowFailure codes and spoken guidance in modules/assistant/workflow.py
- [X] T052 [US3] Implement cleanup-empty and uncertain-cleanup handling before reading handoff in modules/assistant/workflow.py
- [X] T053 [US3] Implement TTS, translation, command-routing, TimeoutError, and unexpected-exception failure mapping in modules/assistant/workflow.py
- [X] T054 [US3] Implement recoverable failure state transitions that preserve previous successful clean text and translated text in modules/assistant/workflow.py
- [X] T055 [US3] Update docs/troubleshooting.md with Phase 9 recovery guidance for busy workflow, recapture, OCR failure, cleanup-empty, translation failure, TTS failure, timeout, and unexpected workflow failure
- [X] T056 [US3] Run focused US3 validation with python -m pytest tests/unit/test_assistant_workflow_failures.py tests/unit/test_assistant_workflow.py

**Checkpoint**: User Stories 1, 2, and 3 work independently and together.

---

## Phase 6: User Story 4 - Stop Safely (Priority: P4)

**Goal**: Support graceful operational shutdown from process interruption, service stop, or test harness control while keeping voice stop as playback control only.

**Independent Test**: Trigger shutdown while idle, listening, capturing, processing OCR, translating, and speaking; verify active speech settlement, camera/audio cleanup hooks, final state, safe metadata, no background workflow, and no new voice exit command.

### Tests for User Story 4

- [X] T057 [P] [US4] Write failing unit tests for shutdown while idle, active read workflow, active translation workflow, and active speech in tests/unit/test_assistant_workflow.py
- [X] T058 [P] [US4] Write failing unit tests proving voice stop remains playback control and does not invoke operational shutdown in tests/unit/test_assistant_workflow.py
- [X] T059 [P] [US4] Write failing unit tests for process interruption, service-stop/test-harness shutdown, cleanup hook failures, and no background workflow after shutdown in tests/unit/test_assistant_workflow_failures.py
- [X] T060 [P] [US4] Write failing tests for main.py signal wiring, workflow factory behavior, no live hardware import side effects, and CLI help behavior in tests/unit/test_main_assistant_entrypoint.py
- [X] T061 [P] [US4] Extend privacy tests proving shutdown logs and final safe metadata exclude text, images, command transcripts, snippets, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py

### Implementation for User Story 4

- [X] T062 [US4] Implement AssistantWorkflow.shutdown operational lifecycle handling, final guidance, workflow_active clearing, and shutdown_requested state in modules/assistant/workflow.py
- [X] T063 [US4] Implement best-effort active speech settlement and injected camera/audio cleanup hooks during shutdown in modules/assistant/workflow.py
- [X] T064 [US4] Ensure handle_command stop intent continues to route only to reading playback control through existing dialogue behavior in modules/assistant/workflow.py
- [X] T065 [US4] Implement main.py signal handling and service/test-harness shutdown entrypoints without starting live hardware at import time
- [X] T066 [US4] Implement shutdown safe metadata and resource-release failure guidance in modules/assistant/state.py and modules/assistant/workflow.py
- [X] T067 [US4] Run focused US4 validation with python -m pytest tests/unit/test_assistant_workflow.py tests/unit/test_assistant_workflow_failures.py tests/unit/test_main_assistant_entrypoint.py tests/unit/test_assistant_workflow_logging_privacy.py

**Checkpoint**: All Phase 9 user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, quickstart alignment, privacy review, scope review, and regression checks across Phase 9.

- [X] T068 [P] Update docs/architecture.md with Phase 9 workflow coordinator boundaries, state lifecycle, read workflow, translation workflow, failure handling, and shutdown behavior
- [X] T069 [P] Update docs/troubleshooting.md with final Phase 9 error categories and recovery guidance discovered during implementation
- [X] T070 [P] Update specs/010-phase9-workflow-integration/quickstart.md with final validation commands, optional hardware acceptance notes, and any unavailable optional tooling notes
- [X] T071 [P] Write Phase 9 scope-boundary tests proving no new OCR engines, translation engines, STT/TTS engines, cleanup rules, command categories, benchmark tooling, deployment services, visual UI, user accounts, or cloud storage were introduced in tests/unit/test_assistant_workflow_scope_boundaries.py
- [X] T072 Run focused Phase 9 validation with python -m pytest tests/unit/test_assistant_state.py tests/unit/test_assistant_workflow.py tests/unit/test_assistant_workflow_failures.py tests/unit/test_assistant_workflow_logging_privacy.py tests/unit/test_assistant_workflow_scope_boundaries.py tests/unit/test_main_assistant_entrypoint.py tests/integration/test_full_read_workflow.py tests/integration/test_full_translate_workflow.py
- [X] T073 Run full unit regression with python -m pytest tests/unit
- [X] T074 Run lint validation with python -m ruff check .
- [X] T075 Run optional formatting/type validation with python -m black --check . and python -m mypy . when installed
- [X] T076 Verify Phase 9 scope, privacy, fallback, latest-state lifecycle, shutdown, quickstart, and no-placeholder completion against specs/010-phase9-workflow-integration/quickstart.md
- [X] T077 Mark all completed tasks in specs/010-phase9-workflow-integration/tasks.md after validation succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational and requires latest clean text state, which can be seeded by mocks or US1
- **User Story 3 (Phase 5)**: Depends on Foundational and can be developed with mocked failure boundaries, but final validation should include US1/US2 state preservation
- **User Story 4 (Phase 6)**: Depends on Foundational and can be developed with mocked active workflow states, but final validation should include US1/US2/US3 behavior
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: Can be tested independently by seeding latest clean text; final integration should validate after US1
- **US3 (P3)**: Can be tested independently with mocked failures; final integration should validate preservation of US1/US2 state
- **US4 (P4)**: Can be tested independently with mocked active workflow states; final integration should validate shutdown across read, translate, and failure states

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Models before services
- State/result contracts before workflow orchestration
- Boundary wrapper behavior before full workflow integration
- Story-specific implementation before documentation and focused validation
- Validate each story before starting the next priority phase

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001
- T007, T009, T011, and T013 can run in parallel after T005 establishes expected state/result behavior
- US1 tests T016, T017, T018, T019, and T020 can run in parallel
- US2 tests T030, T031, T032, T033, T034, and T035 can run in parallel
- US3 tests T043, T044, T045, T046, T047, and T048 can run in parallel
- US4 tests T057, T058, T059, T060, and T061 can run in parallel
- Polish documentation and scope tests T068, T069, T070, and T071 can run in parallel after implementation stabilizes

---

## Parallel Example: User Story 1

```text
Task: "Write failing unit tests for successful Arabic read command workflow ordering in tests/unit/test_assistant_workflow.py"
Task: "Write failing unit tests for successful English read command workflow ordering in tests/unit/test_assistant_workflow.py"
Task: "Write failing unit tests for OCR fallback metadata, selected OCR engine storage, cleanup language storage, and spoken progress guidance in tests/unit/test_assistant_workflow.py"
Task: "Write failing integration tests for a mocked full read workflow from command recognition through reading handoff in tests/integration/test_full_read_workflow.py"
Task: "Write failing privacy tests proving successful read workflow logs and safe metadata exclude image payloads, raw OCR text, clean text, translated text, command transcripts, speech input, snippets, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py"
```

## Parallel Example: User Story 2

```text
Task: "Write failing unit tests for translate-to-English command using latest clean Arabic text in tests/unit/test_assistant_workflow.py"
Task: "Write failing unit tests for translate-to-Arabic command using latest clean English text in tests/unit/test_assistant_workflow.py"
Task: "Write failing tests for no-latest-clean-text translation guidance and no translation boundary call in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests proving failed read attempts do not clear latest clean text before translation in tests/unit/test_assistant_workflow.py"
Task: "Write failing integration tests for read-then-translate-to-English and read-then-translate-to-Arabic flows in tests/integration/test_full_translate_workflow.py"
Task: "Extend privacy tests proving translation workflow logs and safe metadata exclude source clean text, translated text, snippets, command transcripts, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py"
```

## Parallel Example: User Story 3

```text
Task: "Write failing tests for camera open failure, capture timeout, no frame candidates, and camera release failure guidance in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests for all frames rejected by best-frame selection, recapture guidance, and no automatic repeated capture loop in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests for OCR unavailable, OCR timeout, all OCR engines failed, no text detected, and weak OCR result guidance in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests for cleanup-empty text, uncertain cleanup result, TTS failure, translation failure, and command unavailable guidance in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests for component TimeoutError, unexpected exception wrapping, and assistant responsiveness after recoverable failures in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing state preservation tests proving failed read and translation attempts retain previous successful clean text and translated text in tests/unit/test_assistant_workflow.py"
```

## Parallel Example: User Story 4

```text
Task: "Write failing unit tests for shutdown while idle, active read workflow, active translation workflow, and active speech in tests/unit/test_assistant_workflow.py"
Task: "Write failing unit tests proving voice stop remains playback control and does not invoke operational shutdown in tests/unit/test_assistant_workflow.py"
Task: "Write failing unit tests for process interruption, service-stop/test-harness shutdown, cleanup hook failures, and no background workflow after shutdown in tests/unit/test_assistant_workflow_failures.py"
Task: "Write failing tests for main.py signal wiring, workflow factory behavior, no live hardware import side effects, and CLI help behavior in tests/unit/test_main_assistant_entrypoint.py"
Task: "Extend privacy tests proving shutdown logs and final safe metadata exclude text, images, command transcripts, snippets, secrets, and debug artifacts in tests/unit/test_assistant_workflow_logging_privacy.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation for assistant state, workflow results, safe metadata, injected boundaries, and lifecycle guards.
3. Complete Phase 3 US1 read workflow.
4. Stop and validate US1 independently with mocked Arabic read, English read, capture, OCR, cleanup, and reading boundaries.

### Incremental Delivery

1. Deliver US1 so read command completes the full capture-to-reading workflow.
2. Add US2 translation using latest successful clean text and reading handoff.
3. Add US3 recoverable failure handling and state preservation across all integrated boundaries.
4. Add US4 operational shutdown without changing voice stop semantics.
5. Complete documentation, quickstart, lint, optional formatting/type checks, scope validation, and full unit regression.

### Quality Gates

- No task may introduce paid services, mandatory cloud dependency, visual UI requirement, continuous every-frame OCR, full parallel OCR by default, new engines, new command categories, new cleanup rules, benchmark tooling, deployment service files, user accounts, or cloud storage into Phase 9.
- Default logs and safe metadata must never include images, depth maps, raw OCR text, clean text, translated text, command transcripts, speech input, snippets, provider secrets, endpoint credentials, or debug artifact paths.
- Read workflow must use bounded capture, best-frame selection, OCR cascade, cleanup, and reading handoff in order.
- All-frame rejection must end the read attempt with recapture guidance and no automatic capture loop.
- Recoverable failures must preserve previous successful clean text and translated text.
- Voice stop must remain playback control, while shutdown remains process/service/test-harness lifecycle behavior.
