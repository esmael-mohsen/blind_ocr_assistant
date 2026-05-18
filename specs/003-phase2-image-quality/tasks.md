# Tasks: Phase 2 Image Processing and Quality Checking

**Input**: Design documents from `/specs/003-phase2-image-quality/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/image-processing-contract.md, quickstart.md

**Tests**: Required by the feature specification and constitution. Test tasks are listed before implementation tasks for each user story where practical.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: Maps a task to a user story. Setup, foundational, and polish tasks do not use a story label.
- Every task includes an exact repository path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare image-processing module files, deterministic fixture locations, and local image dependency declarations for Phase 2.

- [X] T001 Update local image-processing and test dependencies in `requirements.txt` and `pyproject.toml`
- [X] T002 Create image-processing module files in `modules/image_processing/image_models.py`, `modules/image_processing/quality_checker.py`, `modules/image_processing/preprocessing.py`, and `modules/image_processing/text_region_detector.py`
- [X] T003 [P] Add Phase 2 package exports placeholder in `modules/image_processing/__init__.py`
- [X] T004 [P] Add deterministic fixture directory notes in `tests/fixtures/images/phase2/README.md`
- [X] T005 [P] Add Phase 2 test file placeholders in `tests/unit/test_image_models.py`, `tests/unit/test_quality_checker.py`, `tests/unit/test_preprocessing.py`, `tests/unit/test_text_region_detector.py`, and `tests/unit/test_image_logging_privacy.py`
- [X] T006 Add image-quality configuration defaults for thresholds and debug image saving in `config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared image-processing data contracts, image decoding, guidance, and safe metadata behavior required by every user story.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T007 Add image input, threshold, status, guidance, report, variant, and error model tests in `tests/unit/test_image_models.py`
- [X] T008 Add image input validation and decoding tests for missing, unreadable, unsupported, and invalid image data in `tests/unit/test_image_models.py`
- [X] T009 Add bilingual guidance catalog tests for ready, improve-lighting, hold-steady, increase-contrast, point-to-text, recapture, and invalid-image categories in `tests/unit/test_quality_checker.py`
- [X] T010 Add default image metadata logging privacy tests in `tests/unit/test_image_logging_privacy.py`
- [X] T011 Implement image status enums, guidance models, threshold model, quality report model, variant result model, and error constants in `modules/image_processing/image_models.py`
- [X] T012 Implement image input validation and single-source decoding helpers in `modules/image_processing/image_models.py`
- [X] T013 Implement bilingual guidance catalog and primary guidance lookup in `modules/image_processing/quality_checker.py`
- [X] T014 Implement privacy-safe quality metadata helpers that exclude image bytes, image arrays, OCR text, and debug paths in `modules/image_processing/image_models.py`
- [X] T015 Export Phase 2 image-processing models and public functions from `modules/image_processing/__init__.py`

**Checkpoint**: Shared image-processing contracts are tested and ready for independent story implementation.

---

## Phase 3: User Story 1 - Reject Poor Images With Guidance (Priority: P1) MVP

**Goal**: Detect dark, bright, blurry, low-contrast, no-text, borderline, and acceptable images; block poor or uncertain images; and return actionable Arabic and English guidance.

**Independent Test**: Run the quality checker tests using deterministic generated or safe local fixtures; poor and uncertain images are rejected with bilingual guidance, while acceptable Arabic, English, and mixed-text fixtures pass.

### Tests for User Story 1

- [X] T016 [P] [US1] Add brightness classification tests for dark, bright, and acceptable fixtures in `tests/unit/test_quality_checker.py`
- [X] T017 [P] [US1] Add blur and sharpness classification tests for blurry and acceptable fixtures in `tests/unit/test_quality_checker.py`
- [X] T018 [P] [US1] Add contrast classification tests for low-contrast and acceptable fixtures in `tests/unit/test_quality_checker.py`
- [X] T019 [P] [US1] Add overall quality decision tests for dark, blurry, low-contrast, no-text, borderline, and acceptable fixtures in `tests/unit/test_quality_checker.py`
- [X] T020 [P] [US1] Add bilingual guidance priority tests for multiple simultaneous quality problems in `tests/unit/test_quality_checker.py`
- [X] T021 [P] [US1] Add conservative blocking tests for borderline and uncertain quality categories in `tests/unit/test_quality_checker.py`
- [X] T022 [P] [US1] Add Arabic, English, and mixed-text acceptable fixture coverage in `tests/unit/test_quality_checker.py`

### Implementation for User Story 1

- [X] T023 [US1] Add deterministic image fixture generation helpers for dark, bright, blurry, low-contrast, no-text, borderline, acceptable Arabic, acceptable English, and acceptable mixed cases in `tests/unit/test_quality_checker.py`
- [X] T024 [US1] Implement brightness scoring and status classification in `modules/image_processing/quality_checker.py`
- [X] T025 [US1] Implement blur or sharpness scoring and status classification in `modules/image_processing/quality_checker.py`
- [X] T026 [US1] Implement contrast scoring and status classification in `modules/image_processing/quality_checker.py`
- [X] T027 [US1] Implement basic no-text and uncertain-text quality checks needed by the overall quality report in `modules/image_processing/quality_checker.py`
- [X] T028 [US1] Implement overall quality score, primary issue selection, conservative blocking, and accept/reject/uncertain decision logic in `modules/image_processing/quality_checker.py`
- [X] T029 [US1] Ensure rejected and uncertain quality reports include Arabic and English guidance text in `modules/image_processing/quality_checker.py`
- [X] T030 [US1] Ensure accepted quality reports include all required statuses, score, safe metadata, and ready guidance in `modules/image_processing/quality_checker.py`

**Checkpoint**: User Story 1 is independently testable as the Phase 2 MVP quality gate.

---

## Phase 4: User Story 2 - Prepare OCR-Ready Image Variants (Priority: P2)

**Goal**: Produce named `online_light`, `local_natural`, and `emergency_strong` variants for accepted images while preserving the original image and returning structured per-variant failures when needed.

**Independent Test**: Run preprocessing tests with accepted source fixtures; all three variant names are returned, original input remains unchanged, and rejected images do not automatically enter preprocessing in the normal workflow.

### Tests for User Story 2

- [X] T031 [P] [US2] Add preprocessing contract tests for required variant names in `tests/unit/test_preprocessing.py`
- [X] T032 [P] [US2] Add original image preservation tests for preprocessing calls in `tests/unit/test_preprocessing.py`
- [X] T033 [P] [US2] Add mild lighting and contrast improvement tests that validate category improvement without exact threshold coupling in `tests/unit/test_preprocessing.py`
- [X] T034 [P] [US2] Add per-variant structured failure tests in `tests/unit/test_preprocessing.py`
- [X] T035 [P] [US2] Add normal workflow tests proving rejected images return corrective guidance rather than automatic preprocessing in `tests/unit/test_preprocessing.py`

### Implementation for User Story 2

- [X] T036 [US2] Implement preprocessing variant result construction and per-variant failure mapping in `modules/image_processing/preprocessing.py`
- [X] T037 [US2] Implement `online_light` preprocessing variant in `modules/image_processing/preprocessing.py`
- [X] T038 [US2] Implement `local_natural` preprocessing variant in `modules/image_processing/preprocessing.py`
- [X] T039 [US2] Implement `emergency_strong` preprocessing variant in `modules/image_processing/preprocessing.py`
- [X] T040 [US2] Implement original-image preservation checks and safe variant metadata in `modules/image_processing/preprocessing.py`
- [X] T041 [US2] Implement normal workflow guard that creates variants only after an accepted quality report in `modules/image_processing/preprocessing.py`

**Checkpoint**: User Story 2 can be validated independently without OCR engines, camera hardware, or internet access.

---

## Phase 5: User Story 3 - Estimate Text Presence Before OCR (Priority: P3)

**Goal**: Provide a reusable deterministic text-presence estimator that reports likely, unlikely, and uncertain text cases without running OCR.

**Independent Test**: Run text-region detector tests with prominent text, sparse text, decorative no-text, edge text, and borderline fixtures; the estimator returns stable status and score values for each case.

### Tests for User Story 3

- [X] T042 [P] [US3] Add likely-text estimation tests for prominent Arabic, English, and mixed text-like fixtures in `tests/unit/test_text_region_detector.py`
- [X] T043 [P] [US3] Add unlikely-text estimation tests for blank and decorative non-text fixtures in `tests/unit/test_text_region_detector.py`
- [X] T044 [P] [US3] Add uncertain-text estimation tests for sparse, small, partial, angled, or edge text fixtures in `tests/unit/test_text_region_detector.py`
- [X] T045 [P] [US3] Add determinism tests proving repeated estimator calls return the same status and score for the same input in `tests/unit/test_text_region_detector.py`
- [X] T046 [P] [US3] Add contract tests proving text-presence estimation does not invoke OCR modules in `tests/unit/test_text_region_detector.py`

### Implementation for User Story 3

- [X] T047 [US3] Implement text-presence scoring and likely/unlikely/uncertain status mapping in `modules/image_processing/text_region_detector.py`
- [X] T048 [US3] Implement decorative-pattern and blank-image safeguards in `modules/image_processing/text_region_detector.py`
- [X] T049 [US3] Implement deterministic scoring for sparse, small, partial, angled, and edge text-like inputs in `modules/image_processing/text_region_detector.py`
- [X] T050 [US3] Integrate the reusable text-presence estimator into the overall quality report without invoking OCR in `modules/image_processing/quality_checker.py`
- [X] T051 [US3] Export text-presence estimator functions from `modules/image_processing/__init__.py`

**Checkpoint**: All Phase 2 image-quality and preprocessing stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate Phase 2 boundaries, documentation, quickstart readiness, privacy defaults, and local quality gates.

- [X] T052 [P] Update Phase 2 architecture notes and boundaries in `docs/architecture.md`
- [X] T053 [P] Update image-quality troubleshooting for dark, bright, blurry, low-contrast, no-text, unsupported image, and rejected-image preprocessing cases in `docs/troubleshooting.md`
- [X] T054 [P] Document Phase 2 validation commands, fixture strategy, and optional quality tool behavior in `specs/003-phase2-image-quality/quickstart.md`
- [X] T055 Verify no Phase 2 file implements camera capture, depth analysis, best-frame selection, OCR engine execution, OCR cascade routing, text cleanup, voice commands, TTS playback, or translation in `modules/image_processing/`
- [X] T056 Run local Phase 2 unit tests with `python -m pytest tests/unit` and record pass status in `specs/003-phase2-image-quality/quickstart.md`
- [X] T057 Run `python -m ruff check .` and record pass status or tool absence in `specs/003-phase2-image-quality/quickstart.md`
- [X] T058 Run optional `python -m black --check .` and `python -m mypy .` when installed and record non-blocking status in `specs/003-phase2-image-quality/quickstart.md`
- [X] T059 Verify default validation creates no permanent debug image artifacts in `tests/fixtures/images/phase2/` and record the result in `specs/003-phase2-image-quality/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user-story phases.
- **User Story 1 (Phase 3)**: Depends on Foundational; delivers the image-quality MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational and can be implemented after US1 MVP validation or in parallel after the shared quality contracts exist.
- **User Story 3 (Phase 5)**: Depends on Foundational and can be implemented independently after shared quality contracts exist.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Reject Poor Images With Guidance**: MVP because it blocks unreliable OCR attempts and provides recapture guidance.
- **US2 Prepare OCR-Ready Image Variants**: Independent after shared image models exist; normal workflow guard references the quality report contract.
- **US3 Estimate Text Presence Before OCR**: Independent after shared image models exist; final integration updates the quality report to use the reusable estimator.

### Within Each User Story

- Write tests before implementation tasks in that story.
- Keep image processing independent from camera, OCR, voice, TTS, text cleanup, and translation modules.
- Validate expected failures as structured image-processing results, not uncaught exceptions.
- Confirm default metadata excludes image contents and OCR text before story completion.

### Parallel Opportunities

- T003, T004, and T005 can run in parallel during setup.
- T016 through T022 can run in parallel for US1 tests.
- T031 through T035 can run in parallel for US2 tests.
- T042 through T046 can run in parallel for US3 tests.
- T052, T053, and T054 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
Task: "T016 [P] [US1] Add brightness classification tests for dark, bright, and acceptable fixtures in tests/unit/test_quality_checker.py"
Task: "T017 [P] [US1] Add blur and sharpness classification tests for blurry and acceptable fixtures in tests/unit/test_quality_checker.py"
Task: "T018 [P] [US1] Add contrast classification tests for low-contrast and acceptable fixtures in tests/unit/test_quality_checker.py"
Task: "T020 [P] [US1] Add bilingual guidance priority tests for multiple simultaneous quality problems in tests/unit/test_quality_checker.py"
```

## Parallel Example: User Story 2

```bash
Task: "T031 [P] [US2] Add preprocessing contract tests for required variant names in tests/unit/test_preprocessing.py"
Task: "T032 [P] [US2] Add original image preservation tests for preprocessing calls in tests/unit/test_preprocessing.py"
Task: "T034 [P] [US2] Add per-variant structured failure tests in tests/unit/test_preprocessing.py"
Task: "T035 [P] [US2] Add normal workflow tests proving rejected images return corrective guidance rather than automatic preprocessing in tests/unit/test_preprocessing.py"
```

## Parallel Example: User Story 3

```bash
Task: "T042 [P] [US3] Add likely-text estimation tests for prominent Arabic, English, and mixed text-like fixtures in tests/unit/test_text_region_detector.py"
Task: "T043 [P] [US3] Add unlikely-text estimation tests for blank and decorative non-text fixtures in tests/unit/test_text_region_detector.py"
Task: "T044 [P] [US3] Add uncertain-text estimation tests for sparse, small, partial, angled, or edge text fixtures in tests/unit/test_text_region_detector.py"
Task: "T046 [P] [US3] Add contract tests proving text-presence estimation does not invoke OCR modules in tests/unit/test_text_region_detector.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational image models, decoding, guidance, and safe metadata.
3. Complete Phase 3: User Story 1.
4. Stop and validate poor-image rejection, conservative blocking, and bilingual guidance before adding preprocessing variants or reusable text-region estimation.

### Incremental Delivery

1. Setup plus Foundational establishes shared image input, report, guidance, threshold, variant, and error behavior.
2. US1 validates the local quality gate and recapture guidance independently.
3. US2 validates OCR-preparation variants independently.
4. US3 validates reusable text-presence estimation independently and integrates it into the quality report.
5. Polish verifies Phase 2 boundaries, quickstart readiness, privacy defaults, and local quality checks.

### Validation Commands

```bash
python -m pytest tests/unit
python -m ruff check .
```

Optional when tools are installed:

```bash
python -m black --check .
python -m mypy .
```

## Notes

- Phase 2 must not implement camera capture, depth analysis, best-frame selection, OCR engine execution, OCR cascade routing, text cleanup, voice commands, TTS playback, or translation.
- Tests should assert named categories and decisions rather than exact default threshold numbers.
- Rejected and uncertain images must return corrective guidance instead of automatically entering preprocessing.
- Default logs must include metadata only and exclude image contents, image arrays, OCR text, and debug artifact paths.
