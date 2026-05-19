# Feature Specification: Phase 9 Full Assistive Workflow Integration

**Feature Branch**: `010-phase9-workflow-integration`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 9 with best practices"

## Clarifications

### Session 2026-05-18

- Q: How should the assistant handle a new read command while a read workflow is already active? -> A: Keep one active workflow; reject the new read command with spoken busy guidance and allow playback control or shutdown.
- Q: What counts as a shutdown request in Phase 9? -> A: Use process interruption, service stop, or test harness shutdown only; voice stop remains playback control and no new exit command is added.
- Q: What happens when every frame in a capture burst fails quality checks? -> A: End that read attempt with spoken recapture guidance and wait for an explicit retry or read command; do not auto-loop captures.
- Q: How should slow or stuck workflow components be handled? -> A: Use existing bounded timeouts; treat timeout as a recoverable failure with spoken guidance and safe state preservation.
- Q: How long should latest successful text and translation state remain available? -> A: Preserve latest successful clean text and translation until replaced by a later success or cleared by shutdown.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Read Workflow By Voice (Priority: P1)

As a blind user, I need one recognized read command to guide capture, choose the best frame, extract text, clean the result, and read it aloud so I can access printed text without visual assistance.

**Why this priority**: This is the first complete product workflow and the minimum useful assistive experience.

**Independent Test**: Start the assistant with mocked or configured camera, OCR, cleanup, and reading boundaries; issue a supported Arabic or English read command; verify the workflow progresses through spoken guidance, capture, best-frame selection, OCR, cleanup, and reading in order without requiring a screen.

**Acceptance Scenarios**:

1. **Given** the assistant is listening and the camera can provide acceptable frames, **When** the user says an Arabic read command, **Then** the assistant gives spoken capture status, selects a best frame, extracts text, cleans it, stores it as the latest clean text, and reads it aloud.
2. **Given** the assistant is listening and the camera can provide acceptable frames, **When** the user says an English read command, **Then** the assistant completes the same read workflow and reads the cleaned result aloud.
3. **Given** the selected frame produces weak online OCR, **When** fallback OCR succeeds, **Then** the assistant explains the fallback path in spoken status and reads the accepted cleaned text.

---

### User Story 2 - Translate Latest Read Text By Voice (Priority: P2)

As a blind user, I need translation commands to use the latest cleaned OCR text and read the translation aloud so I can understand Arabic or English material hands-free.

**Why this priority**: Translation is a core promised workflow after the read path has produced reliable clean text.

**Independent Test**: Complete or simulate a successful read workflow that stores latest clean text; issue supported translate-to-Arabic and translate-to-English commands; verify the assistant translates only the latest clean text, stores the latest translation, and reads the translated result aloud.

**Acceptance Scenarios**:

1. **Given** latest clean Arabic text is available, **When** the user asks to translate to English, **Then** the assistant translates that latest clean text and reads the English translation aloud.
2. **Given** latest clean English text is available, **When** the user asks to translate to Arabic, **Then** the assistant translates that latest clean text and reads the Arabic translation aloud.
3. **Given** no latest clean text is available, **When** the user asks for translation, **Then** the assistant says there is no readable text to translate and does not use stale or raw OCR content.

---

### User Story 3 - Recover From Workflow Problems (Priority: P3)

As a blind user, I need every capture, OCR, cleanup, translation, and reading problem to be explained aloud with the next useful action so I can recover without visual debugging.

**Why this priority**: The full workflow touches hardware, network, local engines, and audio output; accessible recovery is required for trust and safety.

**Independent Test**: Simulate poor image quality, no camera frame, no text found, all OCR engines failing, cleanup producing empty text, translation unavailable, reading unavailable, and unexpected component failures; verify each case returns structured failure, spoken guidance, safe state, and no uncaught exception.

**Acceptance Scenarios**:

1. **Given** captured frames are too dark, blurry, angled, too far, or lack visible text, **When** the user requests reading, **Then** the assistant gives specific spoken recapture guidance instead of continuing silently.
2. **Given** all OCR options fail or return unusable text, **When** the read workflow runs, **Then** the assistant explains that no reliable text was found and preserves the previous successful text if one exists.
3. **Given** translation or reading output fails, **When** the user requests that action, **Then** the assistant explains the failure aloud and keeps the session responsive for another command.

---

### User Story 4 - Stop Safely (Priority: P4)

As a blind user or maintainer, I need the assistant to stop gracefully when the running process is interrupted, stopped by its service, or stopped by a test harness so camera, audio, speech, and in-memory session state are left in a safe condition.

**Why this priority**: Long-running assistive software must recover cleanly from operational stop signals, interruptions, and errors on Raspberry Pi hardware.

**Independent Test**: Trigger shutdown from process interruption, service stop, or test harness control while listening, capturing, reading, or translating; verify speech stops when appropriate, hardware resources are released, the session records a safe final status, and no sensitive content is written to default logs. Voice stop commands remain reading playback controls and do not create a new exit command category in this phase.

**Acceptance Scenarios**:

1. **Given** the assistant is idle, **When** shutdown is requested, **Then** it terminates cleanly after spoken confirmation and releases resources.
2. **Given** the assistant is capturing, reading, or translating, **When** shutdown is requested or an interruption occurs, **Then** it stops active work safely, releases resources, and leaves no background workflow running.

### Edge Cases

- The user gives a read command while another read workflow is already active; the assistant must keep the active workflow, reject the new read request with spoken busy guidance, and still allow playback control or shutdown.
- The user gives playback or translation commands before any successful OCR text exists.
- The camera is missing, busy, disconnected, slow, or returns no usable frames.
- Depth data is unavailable even though RGB capture succeeds.
- Image quality guidance rejects every captured frame in a burst; the assistant must end that read attempt with spoken recapture guidance and wait for an explicit retry or read command.
- Online OCR is unavailable, times out, or returns weak text, requiring offline fallback.
- All OCR options fail or produce empty, low-quality, or unusable text.
- Cleanup produces empty text after OCR returns noisy output.
- Translation is requested with mixed, unknown, empty, stale, or unsupported latest text.
- TTS is unavailable, interrupted, or already speaking when new output begins.
- The user says an unknown, ambiguous, or low-confidence command during workflow execution.
- Internet becomes unavailable between command recognition, OCR, and translation.
- An unexpected exception occurs in any integrated module boundary.
- A workflow component times out or becomes unavailable; the assistant must treat this as a recoverable failure with spoken guidance and safe state preservation.
- Process interruption, service stop, or test harness shutdown occurs while listening, capturing, processing OCR, translating, or speaking.
- Default logs must not expose images, raw OCR text, clean text, translations, command transcripts, or snippets.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a main assistant session that listens for supported voice commands and routes them to complete reading, translation, and playback-control behavior while also responding to operational shutdown requests.
- **FR-002**: System MUST start the full read workflow when a supported Arabic or English read command is recognized.
- **FR-003**: System MUST provide spoken status before and during capture so the user knows capture has started, is progressing, or needs correction.
- **FR-004**: System MUST connect the read workflow to best-frame selection rather than processing continuous video or every frame.
- **FR-005**: System MUST evaluate selected capture quality and provide actionable spoken guidance when the image is not acceptable.
- **FR-006**: System MUST connect acceptable captured images to the OCR cascade and preserve the selected OCR result metadata needed for user-safe status and diagnostics.
- **FR-007**: System MUST connect successful OCR output to text cleanup before reading or translation.
- **FR-008**: System MUST read only cleaned text to the user by default and MUST avoid reading raw OCR text unless explicit debug behavior is introduced outside this phase.
- **FR-009**: System MUST store the latest successful raw text, latest successful clean text, latest translated text, detected language, selected OCR engine, fallback use, and current workflow status in session state.
- **FR-010**: System MUST preserve the previous successful latest clean text when a later read attempt fails before producing a new accepted clean result.
- **FR-011**: System MUST route translate-to-Arabic and translate-to-English commands to translation using the latest successful clean text and requested target language.
- **FR-012**: System MUST read successful translations aloud and store them as the latest translated text.
- **FR-013**: System MUST reject translation requests when no latest clean text is available and MUST provide spoken guidance instead of using stale unrelated content or raw OCR text.
- **FR-014**: System MUST route stop, continue, repeat sentence, and repeat paragraph commands to the existing reading behavior when supported by current reading state.
- **FR-015**: System MUST provide spoken feedback for recognized commands, workflow start, capture guidance, OCR progress, fallback use, cleanup result, reading start, translation start, translation completion, unavailable state, recoverable failure, and shutdown.
- **FR-016**: System MUST handle empty, unknown, ambiguous, low-confidence, unsupported, or unavailable commands without triggering unrelated capture, OCR, translation, cleanup, reading, or shutdown behavior.
- **FR-017**: System MUST return structured, user-understandable failures for camera, image quality, OCR, cleanup, translation, TTS, command routing, and unexpected workflow errors.
- **FR-018**: System MUST keep the assistant responsive after recoverable failures so the user can retry, translate previous successful text, control reading, or stop.
- **FR-019**: System MUST release camera and audio resources during normal shutdown, interrupted shutdown, and fatal startup or workflow failures.
- **FR-020**: System MUST stop or safely settle active speech output during shutdown.
- **FR-021**: System MUST maintain privacy-preserving default logs that include workflow events, selected engines, fallback categories, durations, and failure categories without images, raw OCR text, clean text, translations, command transcripts, or snippets.
- **FR-022**: System MUST avoid paid-service dependency and MUST remain usable in degraded offline mode when online OCR, translation, or speech recognition is unavailable.
- **FR-023**: System MUST keep integrated modules behind stable boundaries so workflow orchestration does not depend on engine-specific internals.
- **FR-024**: System MUST avoid introducing new OCR engines, translation engines, speech engines, cleanup rules, command categories, benchmarking features, deployment services, visual UI, user accounts, or cloud storage as part of this phase.
- **FR-025**: System MUST support automated end-to-end workflow tests using mocked or controlled module boundaries and MUST define manual acceptance checks for hardware-dependent behavior.
- **FR-026**: System MUST allow only one active read workflow at a time; additional read commands during an active read workflow MUST return spoken busy guidance without starting another capture or OCR attempt.
- **FR-027**: System MUST treat voice stop commands as reading playback control only and MUST NOT add a new voice exit command category in this phase.
- **FR-028**: System MUST support graceful shutdown from process interruption, service stop, or test harness control.
- **FR-029**: System MUST end a read attempt when all frames in a bounded capture burst fail quality checks, provide spoken recapture guidance, and wait for an explicit retry or read command before capturing again.
- **FR-030**: System MUST treat configured component timeouts as recoverable workflow failures with spoken guidance, safe state preservation, and no uncaught exception.
- **FR-031**: System MUST preserve latest successful clean text and latest successful translated text until each is replaced by a later successful result or cleared by shutdown.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define spoken feedback for each user-facing workflow state.
- **CR-002**: Feature MUST document OCR, translation, STT, and TTS fallback behavior because it connects those workflows into one assistant session.
- **CR-003**: Feature MUST avoid paid-service dependency and keep online services optional with offline fallback or user-understandable degraded behavior.
- **CR-004**: Feature MUST define privacy behavior for images, raw OCR text, clean text, translations, command transcripts, logs, and debug artifacts.
- **CR-005**: Feature MUST define measurable acceptance criteria for Arabic, English, mixed text, fallback paths, failure modes, and the complete assistive read-translate workflow.

### Key Entities *(include if feature involves data)*

- **AssistantSession**: Represents the running assistive session, current workflow status, latest safe command outcome, and shutdown state.
- **WorkflowRequest**: Represents a requested action such as read, translate, playback control, help, or operational shutdown.
- **ReadWorkflowResult**: Represents the result of a read attempt, including capture outcome, quality outcome, OCR outcome, cleanup outcome, spoken guidance, accepted text availability, and failure category.
- **TranslationWorkflowResult**: Represents the result of translating latest clean text, including target language, source language when known, translated text availability, spoken guidance, and failure category.
- **AssistantState**: Represents latest raw text, latest clean text, latest translated text, latest language, latest OCR engine, fallback use, active reading status, internet availability, and safe workflow status.
- **SpokenStatus**: Represents a user-facing message that confirms progress, fallback use, completion, recovery guidance, or shutdown.
- **WorkflowFailure**: Represents structured recoverable or fatal failure categories across command, camera, quality, OCR, cleanup, translation, TTS, and shutdown boundaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of automated happy-path read workflow tests complete command recognition, capture handoff, best-frame selection, OCR handoff, cleanup handoff, state update, and reading handoff in the expected order.
- **SC-002**: 100% of automated Arabic and English read-command scenarios produce spoken workflow status without requiring visual confirmation.
- **SC-003**: 100% of successful read workflows store latest clean text before translation or repeat-related commands can use it.
- **SC-004**: 100% of translation workflow tests use the latest successful clean text and requested target language, then request spoken reading of the translated output.
- **SC-005**: 100% of no-latest-text translation and playback-control tests return spoken unavailable-state guidance without using raw OCR text or stale unrelated content.
- **SC-006**: 100% of simulated poor capture quality, camera failure, no-text, weak OCR, cleanup-empty, translation-failure, TTS-failure, and unexpected-exception tests return structured failures with spoken recovery guidance and no uncaught exceptions.
- **SC-007**: 100% of online-unavailable OCR, translation, or command-recognition simulations either use the configured offline fallback path or report clear degraded-mode guidance.
- **SC-008**: 100% of shutdown tests release camera/audio resources, settle active speech safely, and leave no active workflow running.
- **SC-009**: 100% of default logging privacy tests confirm no images, raw OCR text, clean text, translations, command transcripts, or snippets are written to logs.
- **SC-010**: 100% of scope-boundary tests confirm this phase does not add new OCR engines, translation engines, speech engines, cleanup rules, command categories, benchmarking features, deployment services, visual UI, user accounts, or cloud storage.
- **SC-011**: Manual hardware acceptance demonstrates the Arabic read-then-translate-to-English workflow at least once on the target device or documented equivalent test environment.
- **SC-012**: Manual hardware acceptance demonstrates the English read-then-translate-to-Arabic workflow at least once on the target device or documented equivalent test environment.
- **SC-013**: 100% of active-workflow concurrency tests reject additional read commands with spoken busy guidance and start no second capture or OCR attempt.
- **SC-014**: 100% of all-frames-rejected capture tests end the current read attempt with spoken recapture guidance and perform no automatic repeated capture loop.
- **SC-015**: 100% of simulated component-timeout tests return recoverable failure guidance, preserve previous successful state, and keep the assistant responsive.
- **SC-016**: 100% of shutdown-trigger tests confirm shutdown works through process interruption, service stop, or test harness control without adding a new voice exit command category.
- **SC-017**: 100% of state-lifecycle tests confirm latest successful clean text and translated text remain available until replaced by a later success or cleared by shutdown.

## Assumptions

- Phase 0 through Phase 8 provide the module boundaries for configuration, logging, result patterns, camera capture, frame selection, image quality, OCR cascade, text cleanup, TTS reading, translation, command parsing, recognition fallback, and dialogue routing.
- Phase 9 integrates existing module behavior into one assistant workflow and does not expand engine capability beyond the accepted previous-phase scope.
- Hardware-dependent behavior can be validated manually when real camera or audio devices are unavailable in automated tests.
- Debug image saving and sensitive text logging remain disabled by default and controlled by explicit configuration from earlier phases.
- The assistant remains a local long-running process with no database, user account system, visual UI requirement, or cloud storage.
- When a new read attempt fails, the last successful clean text remains available for translation unless the user or later workflow explicitly clears session state.
- When translation fails, the last successful translated text remains available for repeat or status behavior unless replaced by a later successful translation or cleared by shutdown.
- A read command is not queued while a read workflow is active; the assistant gives spoken busy guidance and keeps the active workflow as the source of truth.
- Shutdown for Phase 9 is an operational lifecycle event, not a new voice command category.
- Spoken feedback may be represented in automated tests as user-facing guidance text passed to the existing speech boundary.
