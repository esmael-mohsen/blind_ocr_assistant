# Feature Specification: Phase 11 Raspberry Pi Deployment Hardening

**Feature Branch**: `012-phase11-pi-deployment`

**Created**: 2026-05-19

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 11 with best practices"

## Clarifications

### Session 2026-05-19

- Q: What readiness states should deployment validation use? -> A: Use Ready, Degraded, Blocked, and Manual Verification Needed states.
- Q: Which diagnostics should run automatically at assistant startup? -> A: Run lightweight startup checks automatically; provide full hardware diagnostics as an explicit maintainer action.
- Q: How should service startup be delivered? -> A: Provide a manual run script and an optional service template disabled by default.
- Q: What default log retention limit should deployment hardening enforce? -> A: Keep normal logs within a 50 MB local budget by default.
- Q: What should deployment validation artifacts contain? -> A: Store privacy-safe local summaries only, with no user images, OCR text, translations, secrets, or private debug paths.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Reliably on Raspberry Pi (Priority: P1)

As a blind user or caregiver, I need the assistant to start reliably on the Raspberry Pi and clearly announce readiness or blockers so the device can be used without visual troubleshooting.

**Why this priority**: The completed assistant only helps users if it starts predictably on target hardware and communicates status through speech.

**Independent Test**: Boot or start the assistant on target hardware and verify lightweight startup checks announce startup progress, readiness state, and any blocking dependency, camera, audio, or network issue in spoken form.

**Acceptance Scenarios**:

1. **Given** the Raspberry Pi has required dependencies and configuration, **When** the assistant is started, **Then** it becomes ready for voice-driven reading and announces readiness.
2. **Given** a required local dependency is missing, **When** startup checks run, **Then** the assistant reports the missing requirement as a Blocked readiness state in an actionable way without crashing silently.
3. **Given** internet access is unavailable at startup, **When** the assistant starts, **Then** it announces Degraded offline mode and keeps local reading capabilities available.

---

### User Story 2 - Validate Camera and Audio Hardware (Priority: P2)

As a maintainer setting up the device, I need clear hardware validation for camera capture and audio input/output so deployment issues can be found before the assistant is handed to a user.

**Why this priority**: Camera and audio are essential assistive interfaces. Hardware problems must be diagnosed safely and repeatably on the Raspberry Pi.

**Independent Test**: Run explicit full hardware diagnostics for camera, speech output, and command input and verify each check produces a Ready, Degraded, Blocked, or Manual Verification Needed result with next-step guidance.

**Acceptance Scenarios**:

1. **Given** the camera is connected and accessible, **When** full camera diagnostics are performed, **Then** the result confirms capture readiness and resource release.
2. **Given** camera access fails or depth support is unavailable, **When** full camera diagnostics are performed, **Then** the result explains whether RGB-only Degraded operation can continue or setup is Blocked until fixed.
3. **Given** audio output and command input are configured, **When** audio diagnostics are performed, **Then** the device confirms that spoken feedback and voice commands are usable or marks any unprovable result as Manual Verification Needed.

---

### User Story 3 - Confirm Offline and Recovery Behavior (Priority: P3)

As a user in an intermittent-network setting, I need the assistant to keep working locally and recover gracefully when internet access changes so reading does not depend on a stable connection.

**Why this priority**: The constitution requires free online-first behavior with offline fallback. Deployment hardening must prove the real device follows that promise.

**Independent Test**: Start and operate the assistant with no internet, temporary internet loss, and restored internet, then verify spoken status and reading behavior remain understandable and recoverable.

**Acceptance Scenarios**:

1. **Given** no internet is available, **When** the assistant starts and a reading command is issued, **Then** online services are skipped and local OCR fallback behavior is used.
2. **Given** internet fails during normal use, **When** a reading workflow reaches an online step, **Then** the assistant explains the fallback and continues with local alternatives when possible.
3. **Given** internet becomes available again, **When** a later workflow starts, **Then** the assistant may use online-first behavior again without requiring a restart.

---

### User Story 4 - Operate as a Safe Long-Running Device (Priority: P4)

As a caregiver or maintainer, I need the assistant to run as a safe device service with bounded logs and clear stop behavior so it can be used repeatedly without filling storage or leaving hardware locked.

**Why this priority**: A Raspberry Pi deployment may run for long periods. Safe startup, shutdown, and logs reduce maintenance burden and protect privacy.

**Independent Test**: Configure the assistant for service-style startup, run repeated start/stop cycles, and verify logs rotate safely while camera and audio resources are released.

**Acceptance Scenarios**:

1. **Given** the optional service template has been intentionally enabled by a maintainer, **When** the Raspberry Pi starts, **Then** the assistant starts or reports a clear service failure that can be diagnosed from local logs.
2. **Given** the assistant is stopped manually or by service control, **When** shutdown occurs, **Then** camera, audio, and long-running work are stopped safely.
3. **Given** logs grow over repeated use, **When** log rotation policy applies, **Then** normal logs stay within the default local retention budget and sensitive user content is not introduced into normal logs.

### Edge Cases

- Raspberry Pi has limited memory while local OCR models are loaded.
- PaddleOCR model loading is slow, fails, or exceeds safe startup expectations.
- Tesseract or language data is missing.
- Camera is disconnected, busy, permission-blocked, or available only in RGB mode.
- Audio output device is muted, missing, busy, or configured incorrectly.
- Microphone input is missing, noisy, or unavailable.
- Internet is unavailable at startup, fails during use, or recovers after a failure.
- Online service keys or URLs are missing while offline fallback is available.
- Service startup is enabled but fails before speech output is ready.
- Logs directory is missing, read-only, full, or contains old oversized files.
- Debug image or sensitive text logging is accidentally enabled on a shared device.
- The assistant is interrupted during OCR, speech, camera capture, startup checks, or shutdown.
- Lightweight startup checks pass but full hardware diagnostics later find a degraded or blocked hardware condition.
- Optional service startup is installed but not intentionally enabled by a maintainer.
- Deployment validation artifacts are requested after a failure that involved private user content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Raspberry Pi deployment readiness workflow that verifies startup readiness before normal unattended use.
- **FR-002**: System MUST report startup status, readiness, degraded operation, manual-verification-needed states, and blocking failures in a form usable without visual confirmation.
- **FR-003**: System MUST classify deployment readiness outcomes using Ready, Degraded, Blocked, and Manual Verification Needed states.
- **FR-004**: System MUST verify memory safety expectations for long-running operation on the target device and report when available memory is below an acceptable deployment threshold.
- **FR-005**: System MUST validate camera capture stability and confirm that camera resources are released after checks or failed captures.
- **FR-006**: System MUST distinguish full camera readiness, RGB-only degraded readiness, and camera unavailable states.
- **FR-007**: System MUST validate local OCR fallback readiness, including whether required offline recognition paths can load and run on the target device.
- **FR-008**: System MUST validate emergency OCR fallback readiness separately from the preferred offline OCR path.
- **FR-009**: System MUST start and remain usable when internet access is unavailable, provided local reading dependencies are available.
- **FR-010**: System MUST recover from temporary internet failure by explaining fallback behavior and continuing with local alternatives when possible.
- **FR-011**: System MUST re-check online availability for later workflows so restored connectivity can be used without restarting the assistant.
- **FR-012**: System MUST validate audio output readiness for spoken feedback before declaring the assistant ready.
- **FR-013**: System MUST validate command input readiness or report that manual/service diagnostics are needed before normal voice operation.
- **FR-014**: System MUST run lightweight startup checks automatically before declaring normal assistant readiness.
- **FR-015**: System MUST provide explicit full hardware diagnostics for maintainers to validate camera, audio, local OCR fallback, internet recovery, and safe shutdown behavior.
- **FR-016**: System MUST provide a repeatable dependency installation and setup guide for Raspberry Pi deployment.
- **FR-017**: System MUST provide a manual run script and an optional service startup template that remains disabled until a maintainer intentionally enables it.
- **FR-018**: System MUST support safe manual stop and service stop behavior that releases camera, audio, and long-running recognition resources.
- **FR-019**: System MUST provide troubleshooting documentation for startup, dependency, camera, audio, internet, OCR fallback, permissions, and service failures.
- **FR-020**: System MUST apply safe local log retention so normal logs stay within a 50 MB local budget by default.
- **FR-021**: System MUST keep normal logs free of raw images, raw OCR text, clean text, translations, secrets, and private debug paths unless explicit debug settings are enabled.
- **FR-022**: System MUST make debug settings visible in deployment checks so accidental privacy-risky settings are reported before normal use.
- **FR-023**: System MUST record deployment validation outcomes locally with enough detail for maintenance while preserving user privacy.
- **FR-024**: System MUST keep deployment validation artifacts to privacy-safe local summaries and MUST exclude user images, OCR text, translations, secrets, and private debug paths.
- **FR-025**: System MUST avoid adding paid services, mandatory cloud storage, user accounts, visual-only setup steps, or a new user workflow beyond deployment readiness and operation hardening.
- **FR-026**: System MUST document manual hardware acceptance steps when automated verification cannot prove camera, microphone, speaker, or service startup behavior.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define required spoken feedback for startup, readiness, degraded mode, and failures.
- **CR-002**: Feature MUST preserve OCR, STT, and TTS fallback behavior and document offline/no-internet deployment behavior.
- **CR-003**: Feature MUST avoid paid-service dependency and treat online services as optional and replaceable during deployment.
- **CR-004**: Feature MUST define privacy behavior for deployment logs, debug artifacts, images, OCR text, translations, and service diagnostics.
- **CR-005**: Feature MUST define measurable acceptance criteria for Raspberry Pi startup, camera readiness, audio readiness, local fallback readiness, no-internet operation, and safe stop behavior.

### Key Entities *(include if feature involves data)*

- **DeploymentReadinessReport**: A privacy-safe local summary of target-device readiness, including startup status, hardware checks, offline readiness, privacy settings, and blocking issues without user images, OCR text, translations, secrets, or private debug paths.
- **HardwareCheckResult**: A result for camera, audio output, audio input, or resource availability using Ready, Degraded, Blocked, or Manual Verification Needed status.
- **DependencyCheckResult**: A result for required local dependencies, model/data availability, environment configuration, and optional online settings.
- **ServiceStartupOption**: A documented startup mode for running the assistant manually or through an optional disabled-by-default service template with safe start and stop behavior.
- **LogRetentionPolicy**: The local rules for keeping normal logs within a 50 MB default budget while excluding sensitive content by default.
- **TroubleshootingEntry**: A documented deployment problem with symptom, likely cause, accessible diagnosis step, and recovery action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a correctly prepared Raspberry Pi, the assistant reaches a ready state and announces readiness in 100% of deployment validation runs.
- **SC-002**: 100% of startup-blocking failures produce an actionable local diagnostic outcome and do not fail silently.
- **SC-003**: 100% of deployment validation outcomes use Ready, Degraded, Blocked, or Manual Verification Needed status.
- **SC-004**: Camera validation reports Ready, Degraded RGB-only, Blocked, or Manual Verification Needed status for 100% of runs and releases camera resources afterward.
- **SC-005**: Audio validation reports spoken-output readiness and command-input readiness or a documented Manual Verification Needed result for 100% of runs.
- **SC-006**: No-internet startup preserves local reading readiness in 100% of runs where local OCR and speech dependencies are available.
- **SC-007**: Temporary internet failure during use triggers a spoken fallback explanation and local fallback attempt in 100% of applicable workflows.
- **SC-008**: Restored internet can be detected for a later workflow without restarting the assistant in deployment validation.
- **SC-009**: Local OCR fallback readiness is validated for preferred offline OCR and emergency fallback paths with clear pass/fail outcomes.
- **SC-010**: Repeated start/stop validation releases camera and audio resources after every cycle.
- **SC-011**: Log retention keeps normal local logs within a 50 MB default budget during repeated operation tests.
- **SC-012**: 100% of normal deployment logs exclude raw images, raw OCR text, clean text, translations, secrets, and private debug paths.
- **SC-013**: 100% of deployment validation artifacts are privacy-safe local summaries that exclude user images, OCR text, translations, secrets, and private debug paths.
- **SC-014**: Deployment documentation covers dependency setup, manual startup, optional service startup, safe stop, camera issues, audio issues, offline mode, service failures, log rotation, and privacy checks.
- **SC-015**: Manual hardware acceptance steps are documented for every readiness area that cannot be fully validated in automated tests.

## Assumptions

- Phase 0 through Phase 10 provide the assistant workflow, OCR engines, offline fallbacks, speech output, voice commands, logging utilities, benchmarks, and troubleshooting foundations needed for deployment hardening.
- Raspberry Pi 4 with 4GB RAM and the Orbbec Astra Pro remain the target deployment hardware.
- Some hardware behavior cannot be fully automated on non-Raspberry Pi development machines, so manual acceptance steps are valid when target hardware is unavailable.
- Deployment hardening verifies and documents existing assistant capabilities; it does not add new OCR engines, paid providers, visual dashboards, user accounts, cloud storage, or model training.
- Online services may be configured, missing, unavailable, or rate-limited; local fallback readiness is required for a deployable device.
- Normal operation remains privacy-preserving, with debug image saving and sensitive text logging disabled unless explicitly configured by a maintainer.
- Lightweight startup checks are intended for every assistant start, while full hardware diagnostics are maintainer-run checks used during setup, troubleshooting, and release acceptance.
- Service startup is optional and disabled by default so maintainers can validate hardware and privacy settings before enabling unattended operation.
