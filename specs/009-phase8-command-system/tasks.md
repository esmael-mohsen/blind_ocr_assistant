# Tasks: Phase 8 Voice Assistant Command System

**Input**: Design documents from `/specs/009-phase8-command-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/command-system-contract.md, quickstart.md

**Tests**: Included because the constitution and feature specification require deterministic validation for Arabic/English fixed commands, online-first/local-fallback recognition, command routing, spoken guidance, privacy-safe logging, latest-only state, and scope boundaries.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed earlier phases
- **[Story]**: User story label, such as [US1], [US2], [US3], or [US4]
- Every task includes exact file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 8 module files, fixtures, and public package exports.

- [X] T001 Create Phase 8 placeholder modules in modules/voice/command_models.py, modules/voice/command_parser.py, modules/voice/vosk_fallback.py, modules/voice/stt_online.py, and modules/assistant/dialogue_manager.py
- [X] T002 [P] Update Phase 8 public exports in modules/voice/__init__.py and modules/assistant/__init__.py
- [X] T003 [P] Create deterministic bilingual command fixture notes in tests/fixtures/voice/command_phrases.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define command data contracts, safe metadata, deterministic parser rules, and recognizer boundaries that all user stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Write failing model tests for CommandRequest, CommandIntent, CommandResult, CommandRecognizer metadata, CommandError, DialogueState, and CommandFeedback in tests/unit/test_command_models.py
- [X] T005 Implement CommandRequest, CommandIntent, CommandResult, CommandError, DialogueState, CommandFeedback, path enums, confidence enums, operation enums, and error-code enums in modules/voice/command_models.py
- [X] T006 [P] Write failing safe-metadata tests proving command models exclude raw speech text, recognized phrase text, command snippets, raw OCR text, clean text, translated text, tokens, and secrets in tests/unit/test_command_models.py
- [X] T007 Implement privacy-safe metadata helpers, phrase length metadata, latest-only state helpers, and stable guidance defaults in modules/voice/command_models.py
- [X] T008 [P] Write failing parser normalization tests for English casing, repeated spaces, punctuation, Arabic punctuation, and simple Arabic diacritics in tests/unit/test_command_parser.py
- [X] T009 Implement deterministic command normalization helpers and curated phrase catalog structure in modules/voice/command_parser.py
- [X] T010 [P] Write failing parser contract tests for unknown command, ambiguous command, low-confidence/noise command, help command, and no phrase leakage in tests/unit/test_command_parser.py
- [X] T011 Implement CommandParser, parse result mapping, unknown/ambiguous/low-confidence handling, help intent handling, and safe metadata in modules/voice/command_parser.py
- [X] T012 [P] Write failing recognizer boundary tests for structured unavailable results, provider exceptions, no-supported-command output, and safe metadata in tests/unit/test_stt_online.py and tests/unit/test_vosk_fallback.py
- [X] T013 Implement CommandRecognizer protocol, MockCommandRecognizer helper, online no-op STT boundary, and recognizer exception mapping in modules/voice/stt_online.py and modules/voice/vosk_fallback.py
- [X] T014 Ensure foundational Phase 8 imports remain stable by updating modules/voice/__init__.py and modules/assistant/__init__.py

**Checkpoint**: Foundation ready. Command models, parser, safe metadata, and recognizer boundaries can be tested without the dialogue manager.

---

## Phase 3: User Story 1 - Start Reading By Voice (Priority: P1) MVP

**Goal**: Recognize Arabic and English read commands, route them to reading when latest clean text is available, and return spoken guidance when text is missing.

**Independent Test**: Provide Arabic and English read phrases with and without latest clean text; verify read intent recognition, reading route calls, spoken confirmation, no-text guidance, and no visual requirement.

### Tests for User Story 1

- [X] T015 [P] [US1] Write failing parser tests for Arabic read command variants and English read command variants in tests/unit/test_command_parser.py
- [X] T016 [P] [US1] Write failing dialogue manager tests for read command with latest clean text, Arabic guidance, English guidance, and no latest text in tests/unit/test_dialogue_manager.py
- [X] T017 [P] [US1] Write failing latest dialogue-state tests proving read command results replace only latest safe command metadata in tests/unit/test_dialogue_manager.py
- [X] T018 [P] [US1] Write failing privacy tests proving read-command logs and metadata exclude raw speech text, recognized phrase text, command snippets, raw OCR text, and clean text in tests/unit/test_command_logging_privacy.py

### Implementation for User Story 1

- [X] T019 [US1] Add Arabic and English read command phrases to the curated catalog in modules/voice/command_parser.py and tests/fixtures/voice/command_phrases.md
- [X] T020 [US1] Implement DialogueManager constructor, latest clean text injection, reading boundary injection, recognizer injection, state initialization, and get_state in modules/assistant/dialogue_manager.py
- [X] T021 [US1] Implement read command routing to the existing reading behavior when latest clean text is available in modules/assistant/dialogue_manager.py
- [X] T022 [US1] Implement no-latest-clean-text guidance for read commands without calling reading behavior in modules/assistant/dialogue_manager.py
- [X] T023 [US1] Implement read-command spoken confirmation and latest safe DialogueState replacement in modules/assistant/dialogue_manager.py
- [X] T024 [US1] Document Phase 8 read-by-voice MVP behavior and privacy expectations in docs/architecture.md
- [X] T025 [US1] Run focused US1 validation with python -m pytest tests/unit/test_command_models.py tests/unit/test_command_parser.py tests/unit/test_dialogue_manager.py tests/unit/test_command_logging_privacy.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Continue With Offline Fixed Commands (Priority: P2)

**Goal**: Attempt optional online recognition first, then local fixed-command fallback when online recognition is disabled, unavailable, timed out, failed, or returns no supported command.

**Independent Test**: Simulate online recognition disabled, unavailable, timeout, failure, and no-supported-command output; verify local fixed-command fallback recognizes supported Arabic and English commands or returns structured recovery guidance.

### Tests for User Story 2

- [X] T026 [P] [US2] Write failing online STT boundary tests for allow_online false, unconfigured provider, timeout, provider failure, no-supported-command output, and safe metadata in tests/unit/test_stt_online.py
- [X] T027 [P] [US2] Write failing Vosk fallback tests for lazy import, missing package, missing model, fixed-command success, recognition failure, and safe metadata in tests/unit/test_vosk_fallback.py
- [X] T028 [P] [US2] Write failing dialogue manager fallback tests for online disabled, unavailable, timeout, failure, no-supported-command output, local success, local disallowed, and all-recognizers failure in tests/unit/test_dialogue_manager.py
- [X] T029 [P] [US2] Extend privacy tests proving fallback and all-recognizer-failure logs exclude raw speech text, recognized phrase text, command snippets, raw OCR text, clean text, and translated text in tests/unit/test_command_logging_privacy.py

### Implementation for User Story 2

- [X] T030 [US2] Implement OnlineSTTRecognizer no-op boundary with allow_online false, unconfigured, timeout, provider failure, no-supported-command, and safe metadata behavior in modules/voice/stt_online.py
- [X] T031 [US2] Implement VoskFallbackRecognizer lazy resource loading, local fixed-command recognition, unavailable-resource failure, recognition failure, and safe metadata behavior in modules/voice/vosk_fallback.py
- [X] T032 [US2] Implement online-first recognition routing and local fallback eligibility in modules/assistant/dialogue_manager.py
- [X] T033 [US2] Implement all-recognizers-failed aggregation with stable CommandError codes and recovery guidance in modules/assistant/dialogue_manager.py
- [X] T034 [US2] Update troubleshooting notes for online STT unavailable, local Vosk unavailable, timeout, no-supported-command, and all-recognizers failure in docs/troubleshooting.md
- [X] T035 [US2] Run focused US2 validation with python -m pytest tests/unit/test_stt_online.py tests/unit/test_vosk_fallback.py tests/unit/test_dialogue_manager.py tests/unit/test_command_logging_privacy.py

**Checkpoint**: User Stories 1 and 2 work independently and together.

---

## Phase 5: User Story 3 - Control Reading Playback By Voice (Priority: P3)

**Goal**: Recognize Arabic and English stop, continue, repeat sentence, and repeat paragraph commands and route them to existing reading behavior with unavailable-state guidance.

**Independent Test**: Provide supported Arabic and English playback-control phrases with reading state present and absent; verify routing, spoken confirmation, unavailable-state guidance, and no accidental command routing for ambiguous phrases.

### Tests for User Story 3

- [X] T036 [P] [US3] Write failing parser tests for Arabic and English stop, continue, repeat sentence, and repeat paragraph variants in tests/unit/test_command_parser.py
- [X] T037 [P] [US3] Write failing dialogue manager tests for stop active, stop inactive, continue available, continue unavailable, repeat sentence available, repeat paragraph available, and repeat unavailable guidance in tests/unit/test_dialogue_manager.py
- [X] T038 [P] [US3] Write failing ambiguity tests proving low-confidence and multi-intent playback phrases return ambiguous or unknown guidance without routing in tests/unit/test_command_parser.py and tests/unit/test_dialogue_manager.py
- [X] T039 [P] [US3] Extend command fixture notes for playback controls, inactive reading state, ambiguous phrases, and low-confidence samples in tests/fixtures/voice/command_phrases.md

### Implementation for User Story 3

- [X] T040 [US3] Add Arabic and English playback-control command phrases to the curated catalog in modules/voice/command_parser.py
- [X] T041 [US3] Implement stop, continue, repeat sentence, and repeat paragraph routing to existing reading behavior in modules/assistant/dialogue_manager.py
- [X] T042 [US3] Implement unavailable reading-state guidance for playback commands without changing prior reading or translation state in modules/assistant/dialogue_manager.py
- [X] T043 [US3] Implement one-confident-intent routing guard for playback commands in modules/voice/command_parser.py and modules/assistant/dialogue_manager.py
- [X] T044 [US3] Run focused US3 validation with python -m pytest tests/unit/test_command_parser.py tests/unit/test_dialogue_manager.py

**Checkpoint**: User Stories 1, 2, and 3 work independently and together.

---

## Phase 6: User Story 4 - Translate By Voice (Priority: P4)

**Goal**: Recognize Arabic and English translation commands, identify the requested target language, and route translation requests to the existing translation behavior using latest clean text.

**Independent Test**: Provide Arabic and English translation command phrases with and without latest clean text; verify target-language recognition, translation routing, spoken confirmation, and no-readable-text guidance.

### Tests for User Story 4

- [X] T045 [P] [US4] Write failing parser tests for Arabic and English translate-to-Arabic and translate-to-English command variants in tests/unit/test_command_parser.py
- [X] T046 [P] [US4] Write failing dialogue manager tests for translate to Arabic, translate to English, latest clean text required, translation boundary unavailable, and translation failure guidance in tests/unit/test_dialogue_manager.py
- [X] T047 [P] [US4] Write failing help command tests proving help returns supported examples and triggers no reading, translation, capture, OCR, or cleanup action in tests/unit/test_command_parser.py and tests/unit/test_dialogue_manager.py
- [X] T048 [P] [US4] Write failing scope-boundary tests proving Phase 8 code does not call camera, OCR, image processing, text cleanup, translation execution directly, TTS engine implementation, or full workflow orchestration in tests/unit/test_command_scope_boundaries.py

### Implementation for User Story 4

- [X] T049 [US4] Add Arabic and English translation and help command phrases to the curated catalog in modules/voice/command_parser.py and tests/fixtures/voice/command_phrases.md
- [X] T050 [US4] Implement target-language mapping for translate-to-Arabic and translate-to-English intents in modules/voice/command_parser.py
- [X] T051 [US4] Implement translation command routing to the existing translation behavior using latest clean text and target language in modules/assistant/dialogue_manager.py
- [X] T052 [US4] Implement no-latest-clean-text, translation-boundary-unavailable, and translation-failure guidance in modules/assistant/dialogue_manager.py
- [X] T053 [US4] Implement help command guidance that returns supported examples without routing any action in modules/assistant/dialogue_manager.py
- [X] T054 [US4] Document Phase 8 translation-by-voice behavior and final scope boundaries in docs/architecture.md
- [X] T055 [US4] Run focused US4 validation with python -m pytest tests/unit/test_command_parser.py tests/unit/test_dialogue_manager.py tests/unit/test_command_scope_boundaries.py

**Checkpoint**: All Phase 8 user stories are independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, quickstart alignment, privacy review, and regression checks across Phase 8.

- [X] T056 [P] Update specs/009-phase8-command-system/quickstart.md with final validation commands and any environment notes discovered during implementation
- [X] T057 [P] Update docs/architecture.md with final Phase 8 command module boundaries, recognition routing, dialogue state, and reading/translation handoff behavior
- [X] T058 [P] Update docs/troubleshooting.md with final Phase 8 error categories, recovery guidance, and optional online/local recognition dependency notes
- [X] T059 Run focused Phase 8 validation with python -m pytest tests/unit/test_command_models.py tests/unit/test_command_parser.py tests/unit/test_vosk_fallback.py tests/unit/test_stt_online.py tests/unit/test_dialogue_manager.py tests/unit/test_command_logging_privacy.py tests/unit/test_command_scope_boundaries.py
- [X] T060 Run full unit regression with python -m pytest tests/unit
- [X] T061 Run lint validation with python -m ruff check .
- [X] T062 Run optional formatting/type validation with python -m black --check . and python -m mypy . when installed
- [X] T063 Verify Phase 8 scope, privacy, fallback, latest-only state, help command behavior, and no-placeholder completion against specs/009-phase8-command-system/quickstart.md
- [X] T064 Mark all completed tasks in specs/009-phase8-command-system/tasks.md after validation succeeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP
- **User Story 2 (Phase 4)**: Depends on Foundational; can be developed independently with mocked recognizers but should validate with US1 read behavior
- **User Story 3 (Phase 5)**: Depends on Foundational; can be developed independently with mocked reading state but naturally integrates after US1 reading routing
- **User Story 4 (Phase 6)**: Depends on Foundational; can be developed independently with mocked translation behavior but should validate alongside US1 latest clean text state
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Foundational
- **US2 (P2)**: No hard dependency on US1 implementation if recognizer routing is tested with mocks, but final validation should include read-command fallback behavior
- **US3 (P3)**: No hard dependency on US1 if reading state is mocked, but final validation should include read-start plus playback controls
- **US4 (P4)**: No hard dependency on US1 if latest clean text is injected directly, but final validation should include read and translation command coexistence

### Within Each User Story

- Write tests first and confirm they fail before implementation
- Implement models and parser helpers before recognizer or dialogue behavior
- Implement recognizer boundaries before fallback orchestration
- Implement dialogue routing before documentation and focused validation
- Validate each story before starting the next priority phase

### Parallel Opportunities

- T002 and T003 can run in parallel after T001
- T006, T008, T010, and T012 can run in parallel after T004 establishes model expectations
- US1 tests T015, T016, T017, and T018 can run in parallel
- US2 tests T026, T027, T028, and T029 can run in parallel
- US3 tests T036, T037, T038, and T039 can run in parallel
- US4 tests T045, T046, T047, and T048 can run in parallel
- Polish documentation tasks T056, T057, and T058 can run in parallel after implementation stabilizes

---

## Parallel Example: User Story 1

```text
Task: "Write failing parser tests for Arabic read command variants and English read command variants in tests/unit/test_command_parser.py"
Task: "Write failing dialogue manager tests for read command with latest clean text, Arabic guidance, English guidance, and no latest text in tests/unit/test_dialogue_manager.py"
Task: "Write failing latest dialogue-state tests proving read command results replace only latest safe command metadata in tests/unit/test_dialogue_manager.py"
Task: "Write failing privacy tests proving read-command logs and metadata exclude raw speech text, recognized phrase text, command snippets, raw OCR text, and clean text in tests/unit/test_command_logging_privacy.py"
```

## Parallel Example: User Story 2

```text
Task: "Write failing online STT boundary tests for allow_online false, unconfigured provider, timeout, provider failure, no-supported-command output, and safe metadata in tests/unit/test_stt_online.py"
Task: "Write failing Vosk fallback tests for lazy import, missing package, missing model, fixed-command success, recognition failure, and safe metadata in tests/unit/test_vosk_fallback.py"
Task: "Write failing dialogue manager fallback tests for online disabled, unavailable, timeout, failure, no-supported-command output, local success, local disallowed, and all-recognizers failure in tests/unit/test_dialogue_manager.py"
Task: "Extend privacy tests proving fallback and all-recognizer-failure logs exclude raw speech text, recognized phrase text, command snippets, raw OCR text, clean text, and translated text in tests/unit/test_command_logging_privacy.py"
```

## Parallel Example: User Story 3

```text
Task: "Write failing parser tests for Arabic and English stop, continue, repeat sentence, and repeat paragraph variants in tests/unit/test_command_parser.py"
Task: "Write failing dialogue manager tests for stop active, stop inactive, continue available, continue unavailable, repeat sentence available, repeat paragraph available, and repeat unavailable guidance in tests/unit/test_dialogue_manager.py"
Task: "Write failing ambiguity tests proving low-confidence and multi-intent playback phrases return ambiguous or unknown guidance without routing in tests/unit/test_command_parser.py and tests/unit/test_dialogue_manager.py"
Task: "Extend command fixture notes for playback controls, inactive reading state, ambiguous phrases, and low-confidence samples in tests/fixtures/voice/command_phrases.md"
```

## Parallel Example: User Story 4

```text
Task: "Write failing parser tests for Arabic and English translate-to-Arabic and translate-to-English command variants in tests/unit/test_command_parser.py"
Task: "Write failing dialogue manager tests for translate to Arabic, translate to English, latest clean text required, translation boundary unavailable, and translation failure guidance in tests/unit/test_dialogue_manager.py"
Task: "Write failing help command tests proving help returns supported examples and triggers no reading, translation, capture, OCR, or cleanup action in tests/unit/test_command_parser.py and tests/unit/test_dialogue_manager.py"
Task: "Write failing scope-boundary tests proving Phase 8 code does not call camera, OCR, image processing, text cleanup, translation execution directly, TTS engine implementation, or full workflow orchestration in tests/unit/test_command_scope_boundaries.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation for command models, parser rules, safe metadata, and recognizer boundaries.
3. Complete Phase 3 US1 read-by-voice behavior.
4. Stop and validate US1 independently with mocked Arabic read, English read, latest clean text available, and no-latest-text cases.

### Incremental Delivery

1. Deliver US1 so latest clean OCR text can be read by voice command.
2. Add US2 online-first/local-fallback recognition without breaking parser behavior.
3. Add US3 playback controls for stop, continue, repeat sentence, and repeat paragraph.
4. Add US4 translation commands and help guidance.
5. Complete documentation, quickstart, lint, optional formatting/type checks, and full unit regression.

### Quality Gates

- No task may introduce paid STT, cloud-only command recognition, open-ended conversation, camera capture, OCR execution, image processing, text cleanup, translation execution, new TTS engine behavior, or full assistant orchestration into Phase 8.
- Default logs and safe metadata must never include raw speech text, recognized phrase text, command snippets, raw OCR text, clean text, translated text, provider secrets, or endpoint credentials.
- Online recognition failures, no-supported-command output, unavailable local resources, and routing failures must return structured results without uncaught recognizer exceptions.
- Local Vosk resources must be lazy-loaded and absent dependencies must produce structured unavailable results.
- Normal dialogue state must keep only latest safe command metadata and guidance, replacing earlier command state on each command attempt.
