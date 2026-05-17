# Tasks: Phase 0 Repository Bootstrap

**Input**: Design documents from `/specs/001-phase0-bootstrap/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md

**Tests**: Required by the feature specification and constitution. Test tasks are listed before implementation tasks for each user story where practical.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps a task to a user story. Setup, foundational, and polish tasks do not use a story label.
- Every task includes an exact repository path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Phase 0 workspace, package folders, documentation placeholders, and dependency files.

- [X] T001 Create root bootstrap files in `main.py`, `config.py`, `requirements.txt`, `.env.example`, and `README.md`
- [X] T002 [P] Create importable package placeholders in `modules/__init__.py`, `modules/assistant/__init__.py`, `modules/camera/__init__.py`, `modules/common/__init__.py`, `modules/image_processing/__init__.py`, `modules/ocr/__init__.py`, `modules/text/__init__.py`, `modules/translation/__init__.py`, and `modules/voice/__init__.py`
- [X] T003 [P] Create test folder placeholders in `tests/unit/.gitkeep`, `tests/integration/.gitkeep`, `tests/fixtures/images/.gitkeep`, `tests/fixtures/text/.gitkeep`, and `tests/benchmark/.gitkeep`
- [X] T004 [P] Create script placeholders in `scripts/install_pi_dependencies.sh` and `scripts/run_assistant.sh`
- [X] T005 [P] Create documentation placeholders in `docs/architecture.md`, `docs/commands.md`, `docs/troubleshooting.md`, and `docs/benchmark_methodology.md`
- [X] T006 Configure Phase 0 dependencies and optional quality tooling entries in `requirements.txt` and `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared bootstrap primitives used by all user stories.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T007 Implement the shared Operation Result type in `modules/common/result.py`
- [X] T008 Implement centralized Phase 0 defaults and runtime directory constants in `config.py`
- [X] T009 Implement privacy-preserving local logging setup in `modules/common/logging.py`
- [X] T010 Implement safe local runtime folder creation in `modules/common/bootstrap.py`
- [X] T011 Implement CLI argument parsing shell for help and self-check in `main.py`
- [X] T012 Add pytest configuration and import path settings in `pyproject.toml`

**Checkpoint**: Shared bootstrap primitives exist and can be imported by user-story work.

---

## Phase 3: User Story 1 - Start From a Clean Project Skeleton (Priority: P1) MVP

**Goal**: A developer can inspect the scaffold, run help, run self-check, and confirm the project starts without OCR, camera, audio, or translation setup.

**Independent Test**: From a fresh checkout, run `python main.py --help`, run `python main.py --self-check`, and verify the repository scaffold is importable without service credentials or hardware.

### Tests for User Story 1

- [X] T013 [P] [US1] Add importability tests for Phase 0 packages in `tests/unit/test_imports.py`
- [X] T014 [P] [US1] Add CLI help contract tests for `python main.py --help` in `tests/unit/test_bootstrap_cli.py`
- [X] T015 [P] [US1] Add bootstrap self-check contract tests for `python main.py --self-check` in `tests/unit/test_bootstrap_cli.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement help output and self-check dispatch in `main.py`
- [X] T017 [US1] Implement self-check import verification in `modules/common/bootstrap.py`
- [X] T018 [US1] Update project purpose, hardware assumptions, free-only policy, and Phase 0 limitations in `README.md`
- [X] T019 [US1] Document Phase 0 architecture boundaries and reserved module placeholders in `docs/architecture.md`
- [X] T020 [US1] Verify no OCR, camera, audio, translation, internet, or paid-service imports are required by `main.py`

**Checkpoint**: User Story 1 is independently usable as the MVP bootstrap.

---

## Phase 4: User Story 2 - Configure Safe Local Defaults (Priority: P2)

**Goal**: A maintainer can review safe defaults, optional credentials, privacy controls, and automatic local folder creation.

**Independent Test**: Review `.env.example` and `config.py`, then run self-check with missing runtime folders and no credentials to verify safe folders are created and no user content is stored or uploaded.

### Tests for User Story 2

- [X] T021 [P] [US2] Add configuration default tests in `tests/unit/test_config.py`
- [X] T022 [P] [US2] Add environment template safety tests in `tests/unit/test_env_template.py`
- [X] T023 [P] [US2] Add runtime folder creation tests in `tests/unit/test_bootstrap_folders.py`
- [X] T024 [P] [US2] Add local operational logging privacy tests in `tests/unit/test_logging.py`

### Implementation for User Story 2

- [X] T025 [US2] Populate optional service keys and safe privacy defaults in `.env.example`
- [X] T026 [US2] Implement typed configuration loading and validation defaults in `config.py`
- [X] T027 [US2] Implement local runtime folder creation for `logs/`, `debug_captures/`, `benchmark_results/`, and `config/` in `modules/common/bootstrap.py`
- [X] T028 [US2] Implement operational-only log formatter and file handler behavior in `modules/common/logging.py`
- [X] T029 [US2] Document configuration, privacy defaults, and local storage policy in `README.md`
- [X] T030 [US2] Document command and configuration usage in `docs/commands.md`

**Checkpoint**: User Story 2 can be validated without credentials, internet, hardware, or user content.

---

## Phase 5: User Story 3 - Verify Development Quality Gates (Priority: P3)

**Goal**: A contributor can run tests and see consistent result, logging, entrypoint, and optional quality-tool behavior.

**Independent Test**: Run `python -m pytest`; confirm tests cover imports, config defaults, local folder creation, logging setup, Operation Result behavior, entrypoint help, and bootstrap self-check.

### Tests for User Story 3

- [X] T031 [P] [US3] Add Operation Result success and failure tests in `tests/unit/test_result.py`
- [X] T032 [P] [US3] Add bootstrap self-check optional tooling tests in `tests/unit/test_quality_tools.py`
- [X] T033 [P] [US3] Add quickstart command validation tests in `tests/unit/test_quickstart_contract.py`

### Implementation for User Story 3

- [X] T034 [US3] Complete Operation Result helpers for success and failure construction in `modules/common/result.py`
- [X] T035 [US3] Add optional quality tool detection to self-check in `modules/common/bootstrap.py`
- [X] T036 [US3] Ensure self-check reports optional quality tooling as non-blocking in `main.py`
- [X] T037 [US3] Document test, lint, format, and type-check commands in `README.md`
- [X] T038 [US3] Draft Raspberry Pi dependency installation notes in `scripts/install_pi_dependencies.sh`
- [X] T039 [US3] Draft assistant run wrapper for later phases in `scripts/run_assistant.sh`

**Checkpoint**: All Phase 0 tests and quality-gate behavior are ready for implementation validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate Phase 0 boundaries, documentation, and Spec Kit readiness.

- [X] T040 [P] Run and document quickstart validation results in `specs/001-phase0-bootstrap/quickstart.md`
- [X] T041 [P] Review README for accessibility-first intent, free-only policy, privacy defaults, and Phase 0 exclusions in `README.md`
- [X] T042 [P] Review documentation placeholders for future OCR, camera, voice, translation, and benchmark phases in `docs/architecture.md`, `docs/commands.md`, `docs/troubleshooting.md`, and `docs/benchmark_methodology.md`
- [X] T043 Verify no Phase 0 file implements OCR, camera capture, voice recognition, text-to-speech, translation, or full assistive workflow behavior in `modules/`, `main.py`, and `config.py`
- [X] T044 Run the full Phase 0 test suite with `python -m pytest` and record pass status in `specs/001-phase0-bootstrap/quickstart.md`
- [X] T045 Run optional quality commands when installed and record non-blocking status in `specs/001-phase0-bootstrap/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user-story phases.
- **User Story 1 (Phase 3)**: Depends on Foundational; delivers the MVP bootstrap.
- **User Story 2 (Phase 4)**: Depends on Foundational and can proceed after or alongside US1 once shared bootstrap files exist.
- **User Story 3 (Phase 5)**: Depends on Foundational and benefits from US1/US2 implementation for full test coverage.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Start From a Clean Project Skeleton**: MVP and first validation target.
- **US2 Configure Safe Local Defaults**: Can be implemented after Foundational; integrates with US1 self-check.
- **US3 Verify Development Quality Gates**: Can be implemented after Foundational; final validation is strongest after US1 and US2.

### Within Each User Story

- Write tests before implementation tasks in that story.
- Keep future engine placeholders importable but behavior-free.
- Keep self-check core failures separate from optional quality-tool warnings.
- Validate each story independently before moving to the next story.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001 starts.
- T013, T014, and T015 can run in parallel for US1 tests.
- T021, T022, T023, and T024 can run in parallel for US2 tests.
- T031, T032, and T033 can run in parallel for US3 tests.
- T040, T041, and T042 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "T013 [P] [US1] Add importability tests for Phase 0 packages in tests/unit/test_imports.py"
Task: "T014 [P] [US1] Add CLI help contract tests for python main.py --help in tests/unit/test_bootstrap_cli.py"
Task: "T015 [P] [US1] Add bootstrap self-check contract tests for python main.py --self-check in tests/unit/test_bootstrap_cli.py"
```

## Parallel Example: User Story 2

```bash
Task: "T021 [P] [US2] Add configuration default tests in tests/unit/test_config.py"
Task: "T022 [P] [US2] Add environment template safety tests in tests/unit/test_env_template.py"
Task: "T023 [P] [US2] Add runtime folder creation tests in tests/unit/test_bootstrap_folders.py"
Task: "T024 [P] [US2] Add local operational logging privacy tests in tests/unit/test_logging.py"
```

## Parallel Example: User Story 3

```bash
Task: "T031 [P] [US3] Add Operation Result success and failure tests in tests/unit/test_result.py"
Task: "T032 [P] [US3] Add bootstrap self-check optional tooling tests in tests/unit/test_quality_tools.py"
Task: "T033 [P] [US3] Add quickstart command validation tests in tests/unit/test_quickstart_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate `python main.py --help` and `python main.py --self-check`.

### Incremental Delivery

1. Setup plus Foundational establishes importable files and shared primitives.
2. US1 proves the repository skeleton and bootstrap entrypoint.
3. US2 adds safe defaults, local folder creation, and privacy-preserving logging.
4. US3 completes test runner behavior and optional quality-tool reporting.
5. Polish verifies Phase 0 boundaries and quickstart readiness.

### Validation Commands

```bash
python main.py --help
python main.py --self-check
python -m pytest
```

Optional when tools are installed:

```bash
python -m ruff check .
python -m black --check .
python -m mypy .
```

## Notes

- Phase 0 must not implement OCR, camera capture, STT, TTS, translation, or full assistive workflow behavior.
- Default logs must be local operational events only.
- Missing optional quality tools must not fail bootstrap self-check.
- Online service credentials must remain optional and unused in Phase 0.
