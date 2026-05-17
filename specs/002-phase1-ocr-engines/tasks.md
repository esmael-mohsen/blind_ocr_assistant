# Tasks: Phase 1 OCR Engine Prototype

**Input**: Design documents from `/specs/002-phase1-ocr-engines/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ocr-engine-contract.md, quickstart.md

**Tests**: Required by the feature specification and constitution. Test tasks are listed before implementation tasks for each user story where practical.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps a task to a user story. Setup, foundational, and polish tasks do not use a story label.
- Every task includes an exact repository path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare OCR module files, test fixture placeholders, and dependency declarations for Phase 1.

- [X] T001 Create OCR module files in `modules/ocr/base.py`, `modules/ocr/ocr_models.py`, `modules/ocr/ocr_space_client.py`, `modules/ocr/paddle_ocr_engine.py`, and `modules/ocr/tesseract_engine.py`
- [X] T002 [P] Add OCR package exports placeholder in `modules/ocr/__init__.py`
- [X] T003 [P] Add small safe fixture placeholders in `tests/fixtures/images/arabic_sample.txt`, `tests/fixtures/images/english_sample.txt`, `tests/fixtures/images/mixed_sample.txt`, `tests/fixtures/images/no_text_sample.txt`, and `tests/fixtures/text/ocr_expected_notes.md`
- [X] T004 [P] Add Phase 1 test file placeholders in `tests/unit/test_ocr_models.py`, `tests/unit/test_ocr_base.py`, `tests/unit/test_ocr_space_client.py`, `tests/unit/test_paddle_ocr_engine.py`, `tests/unit/test_tesseract_engine.py`, `tests/unit/test_ocr_logging_privacy.py`, and `tests/integration/test_ocr_live_optional.py`
- [X] T005 Update OCR-related optional dependencies and test dependencies in `requirements.txt` and `pyproject.toml`
- [X] T006 Add OCR configuration defaults for timeout, retry count, languages, and optional credentials in `config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared OCR data contracts and interface required by every engine.

**CRITICAL**: No user story engine work should begin until this phase is complete.

- [X] T007 Add OCR request/result/error model tests in `tests/unit/test_ocr_models.py`
- [X] T008 Add OCR engine interface contract tests in `tests/unit/test_ocr_base.py`
- [X] T009 Add default OCR metadata logging privacy tests in `tests/unit/test_ocr_logging_privacy.py`
- [X] T010 Implement `OCRRequest`, `OCRResult`, OCR mode values, and stable error code constants in `modules/ocr/ocr_models.py`
- [X] T011 Implement `OCRBaseEngine`, availability contract, duration capture helper, and text classification helper in `modules/ocr/base.py`
- [X] T012 Implement OCR metadata-only logging helper in `modules/ocr/base.py`
- [X] T013 Export shared OCR models and base interface from `modules/ocr/__init__.py`

**Checkpoint**: Shared OCR contracts are tested and ready for independent engine implementations.

---

## Phase 3: User Story 1 - Validate Online OCR Engine Independently (Priority: P1) MVP

**Goal**: The free online OCR engine can be invoked independently, handles missing credentials/provider failures, retries once for transient failures, and skips live tests when free credentials are absent.

**Independent Test**: Run mocked online OCR tests and the optional live test file with no credentials; mocked tests pass and live tests skip without failing local tests.

### Tests for User Story 1

- [X] T014 [P] [US1] Add missing credential and opt-in live-skip tests in `tests/unit/test_ocr_space_client.py`
- [X] T015 [P] [US1] Add mocked online OCR success and malformed response tests in `tests/unit/test_ocr_space_client.py`
- [X] T016 [P] [US1] Add timeout and one-transient-retry tests in `tests/unit/test_ocr_space_client.py`
- [X] T017 [P] [US1] Add optional live online OCR skip behavior in `tests/integration/test_ocr_live_optional.py`

### Implementation for User Story 1

- [X] T018 [US1] Implement online OCR client constructor and credential availability checks in `modules/ocr/ocr_space_client.py`
- [X] T019 [US1] Implement image path/bytes request handling and provider request payload creation in `modules/ocr/ocr_space_client.py`
- [X] T020 [US1] Implement provider response parsing into `OCRResult` in `modules/ocr/ocr_space_client.py`
- [X] T021 [US1] Implement missing credential, timeout, provider error, malformed response, and one-retry failure handling in `modules/ocr/ocr_space_client.py`
- [X] T022 [US1] Ensure online OCR result metadata excludes raw OCR text by default in `modules/ocr/ocr_space_client.py`
- [X] T023 [US1] Document opt-in live online OCR behavior in `docs/commands.md`

**Checkpoint**: User Story 1 is independently testable as the online OCR MVP.

---

## Phase 4: User Story 2 - Validate Local Accuracy OCR Fallback Independently (Priority: P2)

**Goal**: The local accuracy OCR engine is lazy-loaded, works without internet when available, and returns structured failures when the package or model cannot load.

**Independent Test**: Import the project and construct the engine without loading the heavy model; mocked local OCR tests verify lazy loading, success, model-load failure, and weak/no-text classification.

### Tests for User Story 2

- [X] T024 [P] [US2] Add lazy-loading tests for the local accuracy OCR engine in `tests/unit/test_paddle_ocr_engine.py`
- [X] T025 [P] [US2] Add mocked local accuracy success tests in `tests/unit/test_paddle_ocr_engine.py`
- [X] T026 [P] [US2] Add model/package load failure tests in `tests/unit/test_paddle_ocr_engine.py`
- [X] T027 [P] [US2] Add empty and weak OCR output classification tests in `tests/unit/test_paddle_ocr_engine.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement local accuracy OCR engine constructor without heavy model import in `modules/ocr/paddle_ocr_engine.py`
- [X] T029 [US2] Implement lazy model loading boundary in `modules/ocr/paddle_ocr_engine.py`
- [X] T030 [US2] Implement local accuracy recognize behavior and result mapping in `modules/ocr/paddle_ocr_engine.py`
- [X] T031 [US2] Implement `OCR_MODEL_LOAD_ERROR`, `NO_TEXT_DETECTED`, `WEAK_OCR_RESULT`, and unexpected failure handling in `modules/ocr/paddle_ocr_engine.py`
- [X] T032 [US2] Verify project import and `python main.py --help` do not load the local accuracy OCR model in `tests/unit/test_paddle_ocr_engine.py`

**Checkpoint**: User Story 2 can be validated independently without internet or camera hardware.

---

## Phase 5: User Story 3 - Validate Emergency OCR Fallback Independently (Priority: P3)

**Goal**: The emergency OCR engine is independently invokable, supports Arabic/English language expectations, and returns stable errors for missing executable or language data.

**Independent Test**: Mocked emergency OCR tests verify success, missing executable, missing language data, no-text, weak-result, and unreadable-image behavior without requiring camera hardware.

### Tests for User Story 3

- [X] T033 [P] [US3] Add emergency OCR executable availability tests in `tests/unit/test_tesseract_engine.py`
- [X] T034 [P] [US3] Add Arabic/English language data availability tests in `tests/unit/test_tesseract_engine.py`
- [X] T035 [P] [US3] Add mocked emergency OCR success tests in `tests/unit/test_tesseract_engine.py`
- [X] T036 [P] [US3] Add no-text, weak-result, and unexpected failure tests in `tests/unit/test_tesseract_engine.py`

### Implementation for User Story 3

- [X] T037 [US3] Implement emergency OCR engine constructor and executable availability checks in `modules/ocr/tesseract_engine.py`
- [X] T038 [US3] Implement Arabic/English language data availability checks in `modules/ocr/tesseract_engine.py`
- [X] T039 [US3] Implement emergency OCR request execution and result mapping in `modules/ocr/tesseract_engine.py`
- [X] T040 [US3] Implement `OCR_EXECUTABLE_NOT_FOUND`, `OCR_LANGUAGE_DATA_MISSING`, `NO_TEXT_DETECTED`, `WEAK_OCR_RESULT`, and unexpected failure handling in `modules/ocr/tesseract_engine.py`
- [X] T041 [US3] Ensure emergency OCR result metadata excludes raw OCR text by default in `modules/ocr/tesseract_engine.py`

**Checkpoint**: All three OCR engines are independently invokable and return consistent structured results.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate Phase 1 boundaries, documentation, and Spec Kit readiness.

- [X] T042 [P] Update OCR architecture notes and Phase 1 boundaries in `docs/architecture.md`
- [X] T043 [P] Update OCR troubleshooting for missing credentials, model load failure, missing executable, language data, and skipped live tests in `docs/troubleshooting.md`
- [X] T044 [P] Document Phase 1 validation commands and optional live test behavior in `specs/002-phase1-ocr-engines/quickstart.md`
- [X] T045 Verify no Phase 1 file implements camera capture, image-quality pre-checking, best-frame selection, OCR cascade routing, text cleanup, voice commands, TTS, or translation in `modules/`
- [X] T046 Run local Phase 1 unit tests with `python -m pytest tests/unit` and record pass status in `specs/002-phase1-ocr-engines/quickstart.md`
- [X] T047 Run optional live OCR test without credentials and record skip behavior in `specs/002-phase1-ocr-engines/quickstart.md`
- [X] T048 Run optional quality commands when installed and record non-blocking status in `specs/002-phase1-ocr-engines/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all OCR engine user-story phases.
- **User Story 1 (Phase 3)**: Depends on Foundational; delivers the online OCR MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can proceed independently of US1 after shared contracts exist.
- **User Story 3 (Phase 5)**: Depends on Foundational; can proceed independently of US1/US2 after shared contracts exist.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Validate Online OCR Engine Independently**: MVP because the project is online-first.
- **US2 Validate Local Accuracy OCR Fallback Independently**: Independent after shared OCR contracts; validates offline fallback readiness.
- **US3 Validate Emergency OCR Fallback Independently**: Independent after shared OCR contracts; validates graceful degradation.

### Within Each User Story

- Write tests before implementation tasks in that story.
- Keep each engine independent from future cascade orchestration.
- Validate expected failures as structured OCR results, not uncaught exceptions.
- Confirm default OCR metadata excludes raw OCR text before story completion.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel during setup.
- T014, T015, T016, and T017 can run in parallel for US1 tests.
- T024, T025, T026, and T027 can run in parallel for US2 tests.
- T033, T034, T035, and T036 can run in parallel for US3 tests.
- T042, T043, and T044 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "T014 [P] [US1] Add missing credential and opt-in live-skip tests in tests/unit/test_ocr_space_client.py"
Task: "T015 [P] [US1] Add mocked online OCR success and malformed response tests in tests/unit/test_ocr_space_client.py"
Task: "T016 [P] [US1] Add timeout and one-transient-retry tests in tests/unit/test_ocr_space_client.py"
Task: "T017 [P] [US1] Add optional live online OCR skip behavior in tests/integration/test_ocr_live_optional.py"
```

## Parallel Example: User Story 2

```bash
Task: "T024 [P] [US2] Add lazy-loading tests for the local accuracy OCR engine in tests/unit/test_paddle_ocr_engine.py"
Task: "T025 [P] [US2] Add mocked local accuracy success tests in tests/unit/test_paddle_ocr_engine.py"
Task: "T026 [P] [US2] Add model/package load failure tests in tests/unit/test_paddle_ocr_engine.py"
Task: "T027 [P] [US2] Add empty and weak OCR output classification tests in tests/unit/test_paddle_ocr_engine.py"
```

## Parallel Example: User Story 3

```bash
Task: "T033 [P] [US3] Add emergency OCR executable availability tests in tests/unit/test_tesseract_engine.py"
Task: "T034 [P] [US3] Add Arabic/English language data availability tests in tests/unit/test_tesseract_engine.py"
Task: "T035 [P] [US3] Add mocked emergency OCR success tests in tests/unit/test_tesseract_engine.py"
Task: "T036 [P] [US3] Add no-text, weak-result, and unexpected failure tests in tests/unit/test_tesseract_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational OCR contracts.
3. Complete Phase 3: User Story 1.
4. Stop and validate mocked online OCR behavior plus skipped live test behavior.

### Incremental Delivery

1. Setup plus Foundational establishes shared OCR request/result/interface behavior.
2. US1 validates the free online OCR engine independently.
3. US2 validates local accuracy OCR fallback independently.
4. US3 validates emergency OCR fallback independently.
5. Polish verifies Phase 1 boundaries and quickstart readiness.

### Validation Commands

```bash
python -m pytest tests/unit
python -m pytest tests/integration/test_ocr_live_optional.py
```

Optional when tools are installed:

```bash
python -m ruff check .
python -m black --check .
python -m mypy .
```

## Notes

- Phase 1 must not implement camera capture, image-quality pre-checking, best-frame selection, OCR cascade routing, text cleanup, voice commands, TTS, or translation.
- Live online OCR tests are opt-in and skipped without free credentials.
- Heavy local OCR models must not load during import, bootstrap help, or unrelated tests.
- Default OCR logs must include metadata only and exclude raw OCR text.
