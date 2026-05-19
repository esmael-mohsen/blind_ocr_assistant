# Tasks: Phase 11 Raspberry Pi Deployment Hardening

**Input**: Design documents from `/specs/012-phase11-pi-deployment/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/deployment-readiness-contract.md, quickstart.md

**Tests**: Required because Phase 11 touches startup readiness, privacy-safe diagnostics, hardware fallbacks, service startup, log retention, and Raspberry Pi resource behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed foundation tasks
- **[Story]**: Maps to user stories from spec.md
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare deployment module, diagnostics entry point, scripts, service asset location, and documentation placeholders.

- [X] T001 Create deployment package initializer in modules/deployment/__init__.py
- [X] T002 [P] Create deployment diagnostics CLI placeholder in scripts/pi_deployment_check.py
- [X] T003 [P] Create optional service asset directory and template placeholder in deploy/blind-ocr-assistant.service.template
- [X] T004 [P] Review and prepare Raspberry Pi install script for Phase 11 changes in scripts/install_pi_dependencies.sh
- [X] T005 [P] Review and prepare assistant run script for Phase 11 startup checks in scripts/run_assistant.sh
- [X] T006 [P] Create deployment architecture documentation section placeholder in docs/architecture.md
- [X] T007 [P] Create deployment troubleshooting documentation section placeholder in docs/troubleshooting.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core deployment contracts, privacy rules, readiness states, and shared test fixtures that MUST be complete before user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T008 [P] Write failing readiness status and report model tests in tests/unit/test_deployment_readiness_models.py
- [X] T009 [P] Write failing privacy-safe report serialization tests in tests/unit/test_deployment_report_writer.py
- [X] T010 [P] Write failing log retention policy tests for the 50 MB default budget in tests/unit/test_deployment_log_retention.py
- [X] T011 [P] Write failing scope-boundary tests proving Phase 11 adds no OCR engines, translation engines, STT/TTS engines, assistant command categories, visual UI, cloud storage, user accounts, paid services, or auto-enabled service startup in tests/unit/test_deployment_scope_boundaries.py
- [X] T012 [P] Define ReadinessStatus, DeploymentReadinessReport, HardwareCheckResult, DependencyCheckResult, ServiceStartupOption, LogRetentionPolicy, and TroubleshootingEntry models in modules/deployment/readiness_models.py
- [X] T013 Implement readiness severity ordering and overall status aggregation in modules/deployment/readiness_models.py
- [X] T014 Implement privacy-safe report writer with redaction/omission rules in modules/deployment/report_writer.py
- [X] T015 Implement normal-log retention calculations and 50 MB default budget rules in modules/deployment/log_retention.py
- [X] T016 Implement service template safety validation helpers in modules/deployment/service_assets.py
- [X] T017 Add deployment diagnostics output ignore policy for generated deployment_diagnostics artifacts in .gitignore
- [X] T018 Update Phase 11 scope boundaries in docs/architecture.md

**Checkpoint**: Foundation ready. Deployment statuses, privacy-safe report writing, log retention rules, service asset safety, and scope boundaries are defined and tested.

---

## Phase 3: User Story 1 - Start Reliably on Raspberry Pi (Priority: P1) MVP

**Goal**: The assistant can run lightweight startup checks, announce Ready/Degraded/Blocked/Manual Verification Needed status, and start without internet when local reading dependencies are available.

**Independent Test**: Start the assistant or run startup readiness checks with mocked dependencies and verify non-visual readiness output, blocked failure handling, and degraded no-internet behavior.

### Tests for User Story 1

- [X] T019 [P] [US1] Write failing lightweight startup check unit tests for ready, degraded offline, blocked dependency, and manual-verification-needed outcomes in tests/unit/test_deployment_readiness_checks.py
- [X] T020 [P] [US1] Write failing startup diagnostics integration tests with mocked config, folders, network, logs, and privacy settings in tests/integration/test_deployment_diagnostics.py
- [X] T021 [P] [US1] Write failing CLI smoke tests for scripts/pi_deployment_check.py lightweight mode in tests/integration/test_deployment_diagnostics.py

### Implementation for User Story 1

- [X] T022 [P] [US1] Implement configuration, folder, privacy-setting, network, and basic dependency check functions in modules/deployment/readiness_checks.py
- [X] T023 [US1] Implement lightweight startup readiness orchestration in modules/deployment/diagnostics.py
- [X] T024 [US1] Implement privacy-safe lightweight diagnostics CLI output in scripts/pi_deployment_check.py
- [X] T025 [US1] Integrate lightweight startup checks into assistant startup path in main.py
- [X] T026 [US1] Add non-visual startup, degraded, blocked, and manual-verification-needed messages to the assistant startup flow in main.py
- [X] T027 [US1] Ensure no-internet startup reports Degraded when local fallback readiness is available in modules/deployment/readiness_checks.py
- [X] T028 [US1] Persist privacy-safe lightweight readiness summaries through modules/deployment/report_writer.py
- [X] T029 [US1] Document startup readiness states and no-internet startup behavior in docs/troubleshooting.md
- [X] T030 [US1] Verify User Story 1 quickstart commands and update scripts/pi_deployment_check.py help text

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Validate Camera and Audio Hardware (Priority: P2)

**Goal**: Maintainers can run explicit full diagnostics for camera, depth/RGB-only status, speaker output, microphone command input, local OCR fallback readiness, and resource release.

**Independent Test**: Run full diagnostics with mocked camera/audio/OCR boundaries and verify Ready, Degraded, Blocked, or Manual Verification Needed outcomes plus privacy-safe local reports.

### Tests for User Story 2

- [X] T031 [P] [US2] Write failing camera and resource-release diagnostic tests in tests/unit/test_deployment_readiness_checks.py
- [X] T032 [P] [US2] Write failing audio output and command-input diagnostic tests in tests/unit/test_deployment_readiness_checks.py
- [X] T033 [P] [US2] Write failing preferred offline OCR and emergency OCR readiness tests in tests/unit/test_deployment_readiness_checks.py
- [X] T034 [P] [US2] Write failing full diagnostics integration tests with mocked camera, audio, PaddleOCR, Tesseract, and hardware-skipped paths in tests/integration/test_deployment_diagnostics.py

### Implementation for User Story 2

- [X] T035 [P] [US2] Implement camera RGB/depth readiness and RGB-only degraded classification in modules/deployment/readiness_checks.py
- [X] T036 [P] [US2] Implement camera resource release verification in modules/deployment/readiness_checks.py
- [X] T037 [P] [US2] Implement speaker output readiness and manual-verification-needed audio result handling in modules/deployment/readiness_checks.py
- [X] T038 [P] [US2] Implement microphone command-input readiness and manual-verification-needed result handling in modules/deployment/readiness_checks.py
- [X] T039 [P] [US2] Implement preferred offline OCR readiness checks without import-time heavy model loading in modules/deployment/readiness_checks.py
- [X] T040 [P] [US2] Implement emergency OCR fallback readiness checks for Tesseract language data in modules/deployment/readiness_checks.py
- [X] T041 [US2] Add full diagnostics orchestration for camera, audio, local OCR, and skipped-hardware mode in modules/deployment/diagnostics.py
- [X] T042 [US2] Add --full, --skip-hardware, --offline, and --output-dir behavior to scripts/pi_deployment_check.py
- [X] T043 [US2] Write full diagnostics reports and summaries through modules/deployment/report_writer.py
- [X] T044 [US2] Update camera test script notes for Phase 11 diagnostics in scripts/test_camera.py
- [X] T045 [US2] Update TTS test script notes for Phase 11 diagnostics in scripts/test_tts.py
- [X] T046 [US2] Document camera, RGB-only, depth, speaker, microphone, local OCR, and manual verification workflows in docs/troubleshooting.md

**Checkpoint**: User Story 2 can be tested independently through full diagnostics with mocked or real hardware.

---

## Phase 5: User Story 3 - Confirm Offline and Recovery Behavior (Priority: P3)

**Goal**: Deployment diagnostics prove the assistant handles no-internet startup, temporary internet failure, local fallback attempts, and restored online availability without restart.

**Independent Test**: Run offline and recovery diagnostics with mocked network/OCR boundaries and verify spoken fallback summaries, local fallback readiness, and later online re-check behavior.

### Tests for User Story 3

- [X] T047 [P] [US3] Write failing offline startup and local fallback readiness tests in tests/unit/test_deployment_readiness_checks.py
- [X] T048 [P] [US3] Write failing temporary internet failure and restored connectivity tests in tests/integration/test_deployment_diagnostics.py
- [X] T049 [P] [US3] Write failing privacy-safe failure-report tests for online outage scenarios in tests/unit/test_deployment_report_writer.py

### Implementation for User Story 3

- [X] T050 [P] [US3] Implement no-internet startup classification and local fallback dependency checks in modules/deployment/readiness_checks.py
- [X] T051 [P] [US3] Implement temporary internet failure probe and restored-connectivity re-check logic in modules/deployment/readiness_checks.py
- [X] T052 [US3] Integrate offline and recovery checks into full diagnostics orchestration in modules/deployment/diagnostics.py
- [X] T053 [US3] Add --offline behavior and online-disabled safe reporting to scripts/pi_deployment_check.py
- [X] T054 [US3] Add spoken fallback summary mapping for offline and recovery states in main.py
- [X] T055 [US3] Ensure online settings are reported as optional/degraded when local fallback is ready in modules/deployment/readiness_checks.py
- [X] T056 [US3] Document no-internet startup, temporary outage, restored connectivity, and local fallback troubleshooting in docs/troubleshooting.md

**Checkpoint**: User Story 3 independently proves deployment behavior for intermittent network conditions.

---

## Phase 6: User Story 4 - Operate as a Safe Long-Running Device (Priority: P4)

**Goal**: Maintainers can run the assistant with safe manual startup, optional disabled-by-default service startup, safe stop behavior, bounded logs, and privacy-safe deployment artifacts.

**Independent Test**: Validate scripts/service assets, repeated start/stop behavior with mocked resources, log retention within the 50 MB budget, and privacy-safe reports.

### Tests for User Story 4

- [X] T057 [P] [US4] Write failing manual run script and optional service template validation tests in tests/unit/test_deployment_service_assets.py
- [X] T058 [P] [US4] Write failing safe stop and resource-release integration tests in tests/integration/test_deployment_diagnostics.py
- [X] T059 [P] [US4] Write failing log rotation/pruning tests for repeated operation in tests/unit/test_deployment_log_retention.py
- [X] T060 [P] [US4] Write failing privacy-risk debug setting detection tests in tests/unit/test_deployment_readiness_checks.py

### Implementation for User Story 4

- [X] T061 [P] [US4] Implement manual assistant startup wrapper with environment setup and safe stop behavior in scripts/run_assistant.sh
- [X] T062 [P] [US4] Implement Raspberry Pi dependency setup guidance and idempotent install checks in scripts/install_pi_dependencies.sh
- [X] T063 [P] [US4] Implement disabled-by-default service template with safe stop and log guidance in deploy/blind-ocr-assistant.service.template
- [X] T064 [P] [US4] Implement service template inspection and enablement warning helpers in modules/deployment/service_assets.py
- [X] T065 [US4] Integrate safe stop diagnostics and repeated start/stop checks in modules/deployment/diagnostics.py
- [X] T066 [US4] Implement log retention rotate/prune decision support in modules/deployment/log_retention.py
- [X] T067 [US4] Integrate log retention checks and privacy-risk debug setting checks in modules/deployment/readiness_checks.py
- [X] T068 [US4] Add service and log retention checks to full diagnostics CLI output in scripts/pi_deployment_check.py
- [X] T069 [US4] Document manual startup, optional service enable/disable/status/stop, log rotation, and privacy checks in docs/troubleshooting.md
- [X] T070 [US4] Document deployment package boundaries and service asset lifecycle in docs/architecture.md

**Checkpoint**: User Story 4 independently supports long-running Raspberry Pi operation with bounded logs and safe optional service startup.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finish validation, docs, privacy review, and release readiness across all Phase 11 stories.

- [X] T071 [P] Update Phase 11 quickstart with final commands and expected outputs in specs/012-phase11-pi-deployment/quickstart.md
- [X] T072 [P] Update deployment readiness contract with final CLI flags, statuses, report fields, failure categories, and privacy guarantees in specs/012-phase11-pi-deployment/contracts/deployment-readiness-contract.md
- [X] T073 [P] Add manual Raspberry Pi hardware acceptance checklist to docs/troubleshooting.md
- [X] T074 [P] Add deployment hardening summary to README.md
- [X] T075 Run focused Phase 11 tests and record validation results in specs/012-phase11-pi-deployment/quickstart.md
- [X] T076 Run full unit regression and record unavailable optional tooling in specs/012-phase11-pi-deployment/quickstart.md
- [X] T077 Run linting with ruff and fix Phase 11 issues in modules/deployment/
- [X] T078 Perform privacy review for deployment reports, logs, scripts, service template, and diagnostics in modules/deployment/report_writer.py
- [X] T079 Perform Raspberry Pi resource review for startup checks, heavy model loading, log budget, and service behavior in docs/architecture.md
- [X] T080 Verify task completion, scope boundaries, and manual acceptance coverage in specs/012-phase11-pi-deployment/tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 US1**: Depends on Phase 2 and is the MVP.
- **Phase 4 US2**: Depends on Phase 2; may run after or alongside US1 but integrates best after readiness models exist.
- **Phase 5 US3**: Depends on Phase 2; can run alongside US2 after readiness checks exist.
- **Phase 6 US4**: Depends on Phase 2; service/log work can run alongside US2/US3 but final validation benefits from US1 startup integration.
- **Phase 7 Polish**: Depends on all desired user stories.

### User Story Dependencies

- **US1 Start Reliably on Raspberry Pi (P1)**: Independent after foundation; recommended MVP.
- **US2 Validate Camera and Audio Hardware (P2)**: Independent after foundation; uses readiness models and diagnostics orchestration.
- **US3 Confirm Offline and Recovery Behavior (P3)**: Independent after foundation; uses network and fallback readiness checks.
- **US4 Operate as a Safe Long-Running Device (P4)**: Independent after foundation; uses report, log retention, and service asset helpers.

### Within Each User Story

- Write tests first and confirm they fail before implementation.
- Models and helpers before orchestration.
- Orchestration before CLI/script integration.
- CLI/script integration before documentation and manual acceptance notes.
- Privacy-safe reporting must be checked before any generated artifact is considered accepted.

---

## Parallel Opportunities

- T002-T007 can run in parallel after T001.
- T008-T012 can run in parallel because they target separate test/model files.
- T014-T016 can run in parallel after T012-T013.
- US1 tests T019-T021 can run in parallel.
- US2 tests T031-T034 can run in parallel.
- US2 check implementations T035-T040 can run in parallel.
- US3 tests T047-T049 can run in parallel.
- US3 check implementations T050-T051 can run in parallel.
- US4 tests T057-T060 can run in parallel.
- US4 script/service implementations T061-T064 can run in parallel.
- Polish documentation tasks T071-T074 can run in parallel.

---

## Parallel Example: User Story 1

```text
Task: "Write failing lightweight startup check unit tests for ready, degraded offline, blocked dependency, and manual-verification-needed outcomes in tests/unit/test_deployment_readiness_checks.py"
Task: "Write failing startup diagnostics integration tests with mocked config, folders, network, logs, and privacy settings in tests/integration/test_deployment_diagnostics.py"
Task: "Write failing CLI smoke tests for scripts/pi_deployment_check.py lightweight mode in tests/integration/test_deployment_diagnostics.py"
```

## Parallel Example: User Story 2

```text
Task: "Implement camera RGB/depth readiness and RGB-only degraded classification in modules/deployment/readiness_checks.py"
Task: "Implement speaker output readiness and manual-verification-needed audio result handling in modules/deployment/readiness_checks.py"
Task: "Implement preferred offline OCR readiness checks without import-time heavy model loading in modules/deployment/readiness_checks.py"
Task: "Implement emergency OCR fallback readiness checks for Tesseract language data in modules/deployment/readiness_checks.py"
```

## Parallel Example: User Story 4

```text
Task: "Implement manual assistant startup wrapper with environment setup and safe stop behavior in scripts/run_assistant.sh"
Task: "Implement Raspberry Pi dependency setup guidance and idempotent install checks in scripts/install_pi_dependencies.sh"
Task: "Implement disabled-by-default service template with safe stop and log guidance in deploy/blind-ocr-assistant.service.template"
Task: "Implement service template inspection and enablement warning helpers in modules/deployment/service_assets.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 US1 lightweight startup readiness.
4. Stop and validate startup checks, degraded no-internet behavior, blocked dependency behavior, privacy-safe report output, and non-visual status messages.

### Incremental Delivery

1. US1 delivers reliable startup readiness.
2. US2 adds explicit camera/audio/OCR hardware diagnostics.
3. US3 adds no-internet and recovery validation.
4. US4 adds long-running operation hardening, optional service startup, safe stop, and bounded logs.
5. Polish completes docs, validation, privacy review, and resource review.

### Parallel Team Strategy

After Phase 2, different contributors can work on US2, US3, and US4 in parallel if they avoid editing the same files at the same time. Coordinate changes to modules/deployment/readiness_checks.py and modules/deployment/diagnostics.py because multiple stories extend those shared files.

---

## Notes

- [P] tasks touch separate files or can proceed after their listed prerequisites.
- Each user story is independently testable with mocked boundaries and documented manual Raspberry Pi acceptance.
- Do not add OCR, translation, STT, or TTS engines in Phase 11.
- Do not introduce paid services, cloud storage, user accounts, visual UI requirements, or automatic service enablement.
- Default deployment reports and logs must remain privacy-safe.
- Heavy OCR model checks belong in explicit full diagnostics, not lightweight startup.
