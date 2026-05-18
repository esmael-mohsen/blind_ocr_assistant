# Tasks: Phase 3 Camera Integration and Best Frame Selection

**Input**: Design documents from `/specs/004-camera-frame-selection/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Automated tests are required by the accepted specification and constitution for deterministic selection, mocked camera capture, depth guidance, resource cleanup, privacy, and Phase 3 scope boundaries. Write story tests before implementation and confirm they fail for the intended missing behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file or has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- All descriptions include exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 3 camera module structure, fixtures, and optional hardware-test boundaries.

- [X] T001 Create Phase 3 camera package exports in modules/camera/__init__.py
- [X] T002 [P] Create Phase 3 fixture documentation in tests/fixtures/images/phase3/README.md
- [X] T003 [P] Create optional live camera integration test placeholder in tests/integration/test_camera_live_optional.py
- [X] T004 Add Phase 3 camera defaults to config.py for frame count, timeout, depth thresholds, RGB fallback, and debug frame saving

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared contracts and safe primitives that all camera, selection, and depth stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [P] Add failing validation tests for CaptureRequest clamping, timeout validation, and debug defaults in tests/unit/test_camera_models.py
- [X] T006 [P] Add failing validation tests for CameraError, FrameCandidate, FrameScore, and BestFrameSelectionResult safe metadata in tests/unit/test_camera_models.py
- [X] T007 Define camera source, distance, cleanup, and error enums in modules/camera/camera_models.py
- [X] T008 Implement CaptureRequest clamping to 10-20 frames, default count 15, positive bounded timeout validation, and debug-save default false in modules/camera/camera_models.py
- [X] T009 Implement FrameCandidate, FrameScore, DepthReport, CameraError, CaptureBurstResult, and BestFrameSelectionResult data models in modules/camera/camera_models.py
- [X] T010 Add metadata sanitization helpers that exclude image contents, raw arrays, OCR text, secrets, and permanent debug paths in modules/camera/camera_models.py
- [X] T011 Update modules/camera/__init__.py to export the shared Phase 3 camera models and enums
- [X] T012 Run foundational model tests with python -m pytest tests/unit/test_camera_models.py

**Checkpoint**: Camera data contracts and safe defaults are ready; user story implementation can begin.

---

## Phase 3: User Story 1 - Select the Best Frame From a Capture Burst (Priority: P1) MVP

**Goal**: Score a bounded burst of candidate frames and deterministically select the clearest acceptable frame, or return recapture guidance when no candidate is acceptable.

**Independent Test**: Given deterministic candidate frames with varied Phase 2 quality, stability, and optional distance data, the selector chooses the expected frame, returns a score breakdown, handles poor bursts, clamps request counts through shared models, and resolves ties by acceptable quality, then stability, then earliest frame.

### Tests for User Story 1

- [X] T013 [P] [US1] Add failing selector test for choosing the clearly best candidate from a deterministic burst in tests/unit/test_frame_selector.py
- [X] T014 [P] [US1] Add failing selector test for returning NO_ACCEPTABLE_FRAME and recapture guidance when all candidates are poor in tests/unit/test_frame_selector.py
- [X] T015 [P] [US1] Add failing selector test for deterministic repeated selection with identical ordered inputs in tests/unit/test_frame_selector.py
- [X] T016 [P] [US1] Add failing selector test for tie-breaking by acceptable quality, stability, and earliest capture order in tests/unit/test_frame_selector.py
- [X] T017 [P] [US1] Add failing selector test for RGB-only candidates using neutral depth distance behavior in tests/unit/test_frame_selector.py
- [X] T018 [P] [US1] Add failing selector test for safe candidate summaries without RGB image payloads or depth map payloads in tests/unit/test_frame_selector.py

### Implementation for User Story 1

- [X] T019 [US1] Implement frame selector configuration constants and score weighting inputs in modules/camera/frame_selector.py
- [X] T020 [US1] Implement Phase 2 quality report adapter logic for frame candidates in modules/camera/frame_selector.py
- [X] T021 [US1] Implement burst stability scoring based on frame order and image similarity metadata in modules/camera/frame_selector.py
- [X] T022 [US1] Implement total frame scoring from quality score, stability score, and optional distance score in modules/camera/frame_selector.py
- [X] T023 [US1] Implement deterministic tie-break logic by acceptable quality, stability, and earliest capture order in modules/camera/frame_selector.py
- [X] T024 [US1] Implement NO_ACCEPTABLE_FRAME failure result and actionable recapture guidance in modules/camera/frame_selector.py
- [X] T025 [US1] Implement safe candidate score summaries for BestFrameSelectionResult in modules/camera/frame_selector.py
- [X] T026 [US1] Export frame selection API from modules/camera/__init__.py
- [X] T027 [US1] Run User Story 1 validation with python -m pytest tests/unit/test_frame_selector.py tests/unit/test_camera_models.py

**Checkpoint**: User Story 1 is independently complete and provides the Phase 3 MVP.

---

## Phase 4: User Story 2 - Capture RGB Frames and Release Camera Resources (Priority: P2)

**Goal**: Provide a camera abstraction that captures RGB frame candidates from the target source or generic RGB fallback and releases resources after every success, failure, timeout, and cancellation path.

**Independent Test**: With mocked camera sources, the capture layer prefers the target depth source, falls back to generic RGB, returns structured candidates, handles invalid frames and timeouts, scores valid partial-timeout bursts, and releases resources exactly once without requiring physical hardware.

### Tests for User Story 2

- [X] T028 [P] [US2] Add failing camera-source test for preferring target depth source before generic RGB fallback in tests/unit/test_camera_capture.py
- [X] T029 [P] [US2] Add failing camera-source test for falling back to generic RGB when target depth open fails in tests/unit/test_camera_capture.py
- [X] T030 [P] [US2] Add failing camera-source test for successful RGB burst capture returning FrameCandidate ids, timestamps, dimensions, source metadata, and cleanup status in tests/unit/test_camera_capture.py
- [X] T031 [P] [US2] Add failing camera-source test for releasing resources exactly once after success, open failure, capture failure, timeout, and cancellation in tests/unit/test_camera_capture.py
- [X] T032 [P] [US2] Add failing camera-source test for excluding empty, corrupted, or inconsistent frames with stable CAMERA_EMPTY_FRAME or CAMERA_INVALID_FRAME errors in tests/unit/test_camera_capture.py
- [X] T033 [P] [US2] Add failing camera-source test for partial timeout scoring valid captured frames and zero-frame timeout returning CAMERA_CAPTURE_TIMEOUT in tests/unit/test_camera_capture.py
- [X] T034 [P] [US2] Add failing camera script behavior test for non-live mode avoiding hardware requirements in tests/unit/test_camera_script.py

### Implementation for User Story 2

- [X] T035 [US2] Implement camera source protocol, mockable source result types, and source selection helpers in modules/camera/orbbec_camera.py
- [X] T036 [US2] Implement target depth camera adapter boundary with safe unavailable behavior for missing Orbbec SDK or OpenNI2 dependencies in modules/camera/orbbec_camera.py
- [X] T037 [US2] Implement generic OpenCV RGB capture fallback adapter in modules/camera/orbbec_camera.py
- [X] T038 [US2] Implement source selection order that attempts target depth capture before generic RGB fallback in modules/camera/orbbec_camera.py
- [X] T039 [US2] Implement capture_frame validation for empty, unreadable, corrupted, and inconsistent RGB frames in modules/camera/orbbec_camera.py
- [X] T040 [US2] Implement capture_burst with clamped frame count, bounded timeout, partial timeout tracking, candidate creation, and stable failure codes in modules/camera/orbbec_camera.py
- [X] T041 [US2] Implement try-finally or context-manager resource cleanup that releases camera resources exactly once on all terminal paths in modules/camera/orbbec_camera.py
- [X] T042 [US2] Integrate capture_burst with select_best_frame while preserving Phase 3 boundary from OCR and assistant workflow code in modules/camera/orbbec_camera.py
- [X] T043 [US2] Implement developer camera validation script with safe default non-live behavior and explicit --live hardware mode in scripts/test_camera.py
- [X] T044 [US2] Add optional live camera pytest skip behavior gated by explicit environment variable or marker in tests/integration/test_camera_live_optional.py
- [X] T045 [US2] Run User Story 2 validation with python -m pytest tests/unit/test_camera_capture.py tests/unit/test_camera_script.py tests/integration/test_camera_live_optional.py

**Checkpoint**: User Story 2 is independently complete and provides hardware-safe capture with deterministic cleanup.

---

## Phase 5: User Story 3 - Use Depth for Distance Guidance When Available (Priority: P3)

**Goal**: Add optional depth analysis that classifies document distance and improves guidance while preserving RGB-only operation when depth is missing or invalid.

**Independent Test**: Given mocked depth maps and RGB-only candidates, the system classifies too close, acceptable, too far, and unavailable depth states; adjusts frame scoring with deterministic distance contributions; and continues selection when depth is absent.

### Tests for User Story 3

- [X] T046 [P] [US3] Add failing depth test for classifying distance below 25 cm as too_close in tests/unit/test_depth_analyzer.py
- [X] T047 [P] [US3] Add failing depth test for classifying distance from 25 cm through 75 cm as acceptable in tests/unit/test_depth_analyzer.py
- [X] T048 [P] [US3] Add failing depth test for classifying distance above 75 cm as too_far in tests/unit/test_depth_analyzer.py
- [X] T049 [P] [US3] Add failing depth test for missing, noisy, unsupported, unaligned, or invalid depth as unavailable in tests/unit/test_depth_analyzer.py
- [X] T050 [P] [US3] Add failing selector integration test for preserving distance warning when depth conflicts with strong RGB quality in tests/unit/test_frame_selector.py
- [X] T051 [P] [US3] Add failing selector integration test for RGB-only selection succeeding with CAMERA_DEPTH_UNAVAILABLE treated as non-fatal in tests/unit/test_frame_selector.py

### Implementation for User Story 3

- [X] T052 [US3] Implement depth distance extraction and validation helpers in modules/camera/depth_analyzer.py
- [X] T053 [US3] Implement default depth thresholds for too_close, acceptable, too_far, and unavailable status in modules/camera/depth_analyzer.py
- [X] T054 [US3] Implement DepthReport guidance messages and score contributions for each depth status in modules/camera/depth_analyzer.py
- [X] T055 [US3] Integrate depth reports into FrameCandidate creation for target depth captures in modules/camera/orbbec_camera.py
- [X] T056 [US3] Integrate distance score and warning preservation into frame selection in modules/camera/frame_selector.py
- [X] T057 [US3] Export depth analysis API from modules/camera/__init__.py
- [X] T058 [US3] Run User Story 3 validation with python -m pytest tests/unit/test_depth_analyzer.py tests/unit/test_frame_selector.py

**Checkpoint**: User Story 3 is independently complete and depth guidance degrades safely to RGB-only mode.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify privacy, scope, documentation, and whole-Phase 3 validation after all selected stories are complete.

- [X] T059 [P] Add Phase 3 privacy log tests for safe metadata and no image contents, depth arrays, OCR text, or permanent debug paths in tests/unit/test_camera_logging_privacy.py
- [X] T060 [P] Add Phase 3 scope-boundary tests preventing OCR, OCR cascade, text cleanup, voice command, TTS, translation, and assistant workflow calls in tests/unit/test_camera_scope_boundaries.py
- [X] T061 Update docs/architecture.md with Phase 3 camera capture, source fallback, depth guidance, and best-frame selection boundaries
- [X] T062 [P] Update docs/troubleshooting.md with camera unavailable, RGB fallback, timeout, depth unavailable, and cleanup failure guidance
- [X] T063 [P] Update quickstart validation notes in specs/004-camera-frame-selection/quickstart.md with actual test commands and optional live camera command
- [X] T064 Run full Phase 3 unit validation with python -m pytest tests/unit
- [X] T065 Run optional quality validation with python -m ruff check .
- [X] T066 Run optional formatter/type checks when installed with python -m black --check . and python -m mypy .
- [X] T067 Run optional live hardware validation with python scripts/test_camera.py --live only on a machine with camera hardware
- [X] T068 Mark completed tasks in specs/004-camera-frame-selection/tasks.md after each task is implemented and validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational and may call US1 selection integration after US1 is available, while mocked capture behavior remains independently testable.
- **User Story 3 (Phase 5)**: Depends on Foundational and can be implemented independently; final selector integration depends on US1 scoring hooks.
- **Polish (Phase 6)**: Depends on completed selected user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 or US3 after Foundational.
- **US2 (P2)**: Can validate camera capture independently with mocks; full selected-frame capture result integrates with US1.
- **US3 (P3)**: Can validate depth classification independently; distance-aware selection integrates with US1 and candidate creation integrates with US2.

### Within Each User Story

- Tests must be written before implementation and fail for the missing behavior.
- Shared models and configuration must precede selection, capture, and depth services.
- Story-specific implementation must pass its independent validation command before moving to the next story.
- Resource cleanup, privacy defaults, and Phase 3 scope boundaries must remain intact for every story.

## Parallel Opportunities

- Setup tasks T002 and T003 can run in parallel with T001.
- Foundational tests T005 and T006 can run in parallel before model implementation.
- US1 tests T013-T018 can be written in parallel because they target independent selector behaviors.
- US2 tests T028-T034 can be written in parallel because they cover distinct camera and script behaviors.
- US3 tests T046-T051 can be written in parallel because they cover distinct depth and integration cases.
- Documentation polish tasks T062 and T063 can run in parallel with privacy and scope-boundary tests T059 and T060.

## Parallel Example: User Story 1

```text
Task: "T013 [P] [US1] Add failing selector test for choosing the clearly best candidate from a deterministic burst in tests/unit/test_frame_selector.py"
Task: "T014 [P] [US1] Add failing selector test for returning NO_ACCEPTABLE_FRAME and recapture guidance when all candidates are poor in tests/unit/test_frame_selector.py"
Task: "T015 [P] [US1] Add failing selector test for deterministic repeated selection with identical ordered inputs in tests/unit/test_frame_selector.py"
Task: "T016 [P] [US1] Add failing selector test for tie-breaking by acceptable quality, stability, and earliest capture order in tests/unit/test_frame_selector.py"
```

## Parallel Example: User Story 2

```text
Task: "T028 [P] [US2] Add failing camera-source test for preferring target depth source before generic RGB fallback in tests/unit/test_camera_capture.py"
Task: "T031 [P] [US2] Add failing camera-source test for releasing resources exactly once after success, open failure, capture failure, timeout, and cancellation in tests/unit/test_camera_capture.py"
Task: "T034 [P] [US2] Add failing camera script behavior test for non-live mode avoiding hardware requirements in tests/unit/test_camera_script.py"
```

## Parallel Example: User Story 3

```text
Task: "T046 [P] [US3] Add failing depth test for classifying distance below 25 cm as too_close in tests/unit/test_depth_analyzer.py"
Task: "T047 [P] [US3] Add failing depth test for classifying distance from 25 cm through 75 cm as acceptable in tests/unit/test_depth_analyzer.py"
Task: "T049 [P] [US3] Add failing depth test for missing, noisy, unsupported, unaligned, or invalid depth as unavailable in tests/unit/test_depth_analyzer.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational camera models and defaults.
3. Complete Phase 3 User Story 1 frame selection.
4. Validate with `python -m pytest tests/unit/test_frame_selector.py tests/unit/test_camera_models.py`.
5. Stop and confirm deterministic best-frame selection before adding live capture concerns.

### Incremental Delivery

1. Setup plus foundational models.
2. US1 best-frame selection MVP.
3. US2 camera abstraction, capture, fallback, cleanup, and script.
4. US3 optional depth guidance and RGB-only degradation.
5. Polish with privacy, scope-boundary, docs, full unit validation, and optional hardware validation.

### Parallel Team Strategy

1. Complete Setup and Foundational phases together.
2. Implement US1 selection and US3 depth classification in parallel after shared models exist.
3. Implement US2 camera adapters separately from selector internals, then integrate selected-frame capture results.
4. Reserve final polish for cross-story privacy, scope, docs, and validation.

## Notes

- [P] tasks touch independent files or test cases and can be parallelized after their phase prerequisites.
- Hardware-dependent work remains opt-in or manually gated.
- Do not introduce OCR execution, OCR cascade routing, text cleanup, voice commands, TTS, translation, or full assistant workflow behavior in Phase 3.
- Keep debug frame saving disabled by default and avoid permanent captured-frame artifacts during automated validation.
