# Feature Specification: Phase 8 Voice Assistant Command System

**Feature Branch**: `009-phase8-command-system`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 8 with best practices"

## Clarifications

### Session 2026-05-18

- Q: What is the default online/local recognition routing policy? -> A: Use online recognition first when allowed and available; use local fixed-command fallback when online is disabled, unavailable, times out, fails, or returns no supported command.
- Q: How should supported command phrases be matched? -> A: Use a curated Arabic and English phrase catalog with deterministic normalization; avoid open-ended fuzzy guessing.
- Q: What command intents are in scope for Phase 8? -> A: Read, stop, continue, repeat sentence, repeat paragraph, translate to Arabic, translate to English, and help are supported; capture workflow commands are deferred.
- Q: How should low-confidence or multi-intent recognition behave? -> A: Do not route a command unless exactly one supported intent is confidently recognized; otherwise return ambiguous or unknown guidance.
- Q: How long may command transcripts be retained? -> A: Discard raw speech and recognized phrase text after classification; retain only latest safe command metadata.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Reading By Voice (Priority: P1)

As a blind user, I need the assistant to recognize Arabic and English read commands and confirm the command aloud so I can start reading the latest available text without using a screen or keyboard.

**Why this priority**: Voice-initiated reading is the central value of the command system and the minimum useful command workflow.

**Independent Test**: Provide representative Arabic and English read phrases with latest clean text available; verify the assistant recognizes the read intent, does not require visual confirmation, requests reading of the latest clean text, and returns spoken confirmation. Repeat with no latest text and verify helpful guidance instead of a failed or silent command.

**Acceptance Scenarios**:

1. **Given** latest clean text is available, **When** the user says an Arabic read command, **Then** the assistant recognizes a read intent and confirms that reading is starting.
2. **Given** latest clean text is available, **When** the user says an English read command, **Then** the assistant recognizes a read intent and confirms that reading is starting.
3. **Given** no latest clean text is available, **When** the user asks the assistant to read, **Then** the assistant does not start unrelated actions and says that no readable text is available yet.

---

### User Story 2 - Continue With Offline Fixed Commands (Priority: P2)

As a blind user, I need the assistant to recognize the supported command set locally when online speech recognition is unavailable, so basic reading control still works without internet access.

**Why this priority**: The constitution requires free, optional online services with local fallback, and voice control must not disappear when connectivity is weak.

**Independent Test**: Simulate online speech recognition disabled, unavailable, timed out, or failed; provide fixed Arabic and English command phrases; verify the local recognizer identifies supported commands and returns user-safe guidance for unrecognized speech.

**Acceptance Scenarios**:

1. **Given** online speech recognition is unavailable, **When** the user says a supported Arabic command, **Then** the assistant recognizes the command through the local fallback.
2. **Given** online speech recognition is unavailable, **When** the user says a supported English command, **Then** the assistant recognizes the command through the local fallback.
3. **Given** online and local recognition cannot identify the phrase, **When** the user speaks, **Then** the assistant gives helpful spoken guidance instead of failing silently.

---

### User Story 3 - Control Reading Playback By Voice (Priority: P3)

As a blind user, I need voice commands for repeat, stop, and continue so I can control reading without locating visual controls.

**Why this priority**: Reading control is required for practical use after read-aloud exists, especially for rereading important sentences or stopping speech quickly.

**Independent Test**: Provide supported Arabic and English repeat, stop, and continue phrases with reading state present and absent; verify each recognized command is routed to the reading behavior, returns spoken confirmation, and handles inactive or missing reading state gracefully.

**Acceptance Scenarios**:

1. **Given** reading is active, **When** the user says a stop command, **Then** the assistant stops reading and confirms the stop.
2. **Given** repeat history exists, **When** the user says a repeat command, **Then** the assistant repeats the requested recent text segment and confirms the action.
3. **Given** there is no active or resumable reading state, **When** the user says continue, **Then** the assistant explains that there is no reading to continue.

---

### User Story 4 - Translate By Voice (Priority: P4)

As a blind user, I need Arabic and English voice commands that request translation of the latest clean text, so I can ask for Arabic-to-English or English-to-Arabic translation hands-free.

**Why this priority**: Translation is valuable after reading controls are available, and it must reuse the latest clean text rather than asking the user to handle text manually.

**Independent Test**: Provide Arabic and English translation command phrases with latest clean text available; verify the assistant recognizes the requested target language, requests translation of the latest clean text, and returns spoken confirmation or recovery guidance.

**Acceptance Scenarios**:

1. **Given** latest clean text is available, **When** the user asks to translate to English, **Then** the assistant recognizes the target language and confirms translation is starting or ready.
2. **Given** latest clean text is available, **When** the user asks to translate to Arabic, **Then** the assistant recognizes the target language and confirms translation is starting or ready.
3. **Given** no latest clean text is available, **When** the user requests translation, **Then** the assistant says that there is no readable text to translate.

### Edge Cases

- Empty, silence-only, or noise-only speech input must return spoken guidance without triggering a command.
- Unknown commands must produce helpful voice feedback with examples of supported commands.
- Ambiguous commands that could mean more than one action must ask for a clearer command instead of guessing.
- Low-confidence recognition must be treated as unknown or ambiguous and must not route an action.
- Arabic and English command variants must remain fixed and predictable; open-ended conversation is out of scope for this phase.
- Online speech recognition disabled, unavailable, timed out, failed, or returning no supported command must fall back to local fixed-command recognition when allowed.
- If both recognition paths fail, the assistant must return a structured failure and spoken recovery guidance.
- Commands that require latest clean text must not use raw OCR text or stale unrelated content.
- Commands that require reading or translation state must handle missing state with spoken guidance.
- Commands that cannot be routed because required state is unavailable must not change the prior reading, translation, or command state except for latest safe command feedback.
- Default logs must not include raw speech text, recognized phrase text, raw OCR text, clean text, translated text, or snippets.
- This phase must not capture camera frames, run OCR, process images, clean OCR text, perform translation itself, synthesize new speech behavior, or orchestrate the complete end-to-end assistant workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept short Arabic and English voice command phrases from a curated fixed-command catalog for supported assistant actions.
- **FR-002**: System MUST recognize read commands in Arabic and English.
- **FR-003**: System MUST recognize translation commands that request Arabic or English as the target language.
- **FR-004**: System MUST recognize stop, continue, repeat sentence, and repeat paragraph reading-control commands.
- **FR-005**: System MUST return a structured recognized command result, ambiguous command result, unknown command result, or recognition failure result for every command attempt.
- **FR-006**: System MUST provide user-safe spoken confirmation for recognized commands.
- **FR-007**: System MUST provide helpful spoken guidance for unknown, ambiguous, unsupported, empty, failed, or help command recognition.
- **FR-008**: System MUST use online recognition first when allowed and available, and MUST use local fixed-command recognition when online recognition is disabled, unavailable, times out, fails, is not configured, or returns no supported command.
- **FR-009**: System MUST avoid paid-service dependency; any online speech recognition path must be optional, free or replaceable, and not required for fixed commands.
- **FR-010**: System MUST route read, repeat, stop, and continue intents to the existing reading behavior when the required state is available.
- **FR-011**: System MUST route translation intents to the existing translation behavior using the latest clean text and requested target language.
- **FR-012**: System MUST avoid using raw OCR text for command routing or translation requests.
- **FR-013**: System MUST keep command recognition scoped to a controlled command set and MUST NOT introduce open-ended natural language conversation.
- **FR-014**: System MUST support Arabic and English command variants for every supported command intent.
- **FR-015**: System MUST keep only the latest command state needed for feedback and recovery during normal operation.
- **FR-016**: System MUST exclude raw speech text, recognized phrase text, raw OCR text, clean text, translated text, and snippets from default logs.
- **FR-017**: System MUST expose command recognition and command routing as stable boundaries so recognition options can be replaced without changing reading or translation behavior.
- **FR-018**: System MUST return structured guidance when a command depends on unavailable latest text, reading state, or translation state.
- **FR-019**: System MUST remain scoped to command recognition, command intent parsing, command routing, and spoken confirmations only.
- **FR-020**: System MUST route an action only when exactly one supported command intent is confidently recognized.
- **FR-021**: System MUST discard raw speech and recognized phrase text after classification and retain only latest safe command metadata.
- **FR-022**: System MUST support a help intent that returns examples of the fixed Arabic and English command set without triggering reading, translation, capture, OCR, or cleanup actions.
- **FR-023**: System MUST defer capture workflow commands to the later full workflow integration phase.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define spoken feedback for recognized, unknown, ambiguous, failed, and unavailable-state commands.
- **CR-002**: Feature MUST document speech-recognition fallback behavior because it touches the voice-command workflow.
- **CR-003**: Feature MUST avoid paid-service dependency; online recognition must be optional and replaceable, with local fixed-command fallback.
- **CR-004**: Feature MUST define privacy behavior for speech input, recognized phrases, OCR text, translations, logs, and debug artifacts.
- **CR-005**: Feature MUST define measurable acceptance criteria for Arabic commands, English commands, fallback recognition, command routing, unknown commands, and relevant failure modes.

### Key Entities *(include if feature involves data)*

- **CommandRequest**: Represents a single spoken or text-level command attempt, including language hint, online permission, local fallback permission, and operation context.
- **CommandIntent**: Represents the recognized user intention, such as read, stop, continue, repeat sentence, repeat paragraph, translate to Arabic, translate to English, help, unknown, or ambiguous.
- **CommandResult**: Represents recognition success or failure, confidence category, selected recognition path, fallback use, target language when relevant, routed action status, and user-safe guidance.
- **CommandRecognizer**: Represents a replaceable recognition boundary that can identify fixed commands or return structured failure.
- **DialogueState**: Represents latest command status, last recognized intent, selected recognition path, fallback use, and last spoken guidance without retaining raw speech or recognized phrase text.
- **CommandFeedback**: Represents spoken confirmation or recovery guidance for recognized, unknown, ambiguous, failed, or unavailable-state commands.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of supported Arabic read-command test phrases are recognized as read commands.
- **SC-002**: 100% of supported English read-command test phrases are recognized as read commands.
- **SC-003**: 100% of supported Arabic and English translation command test phrases identify the requested target language.
- **SC-004**: 100% of supported repeat, stop, and continue command test phrases are recognized and routed to the reading-control behavior or return appropriate unavailable-state guidance.
- **SC-005**: 100% of simulated online recognition disabled, unavailable, timed-out, failed, or no-supported-command cases attempt local fixed-command recognition when local fallback is allowed.
- **SC-006**: 100% of unknown, ambiguous, low-confidence, or unsupported command test phrases return helpful spoken guidance without triggering reading, translation, capture, OCR, or cleanup actions.
- **SC-007**: 100% of empty, silence-only, or noise-only command attempts return structured no-command guidance without uncaught exceptions.
- **SC-008**: 100% of command routing tests confirm read commands use latest clean text and translation commands use latest clean text plus requested target language.
- **SC-009**: Default logs contain no raw speech text, recognized phrase text, raw OCR text, clean text, translated text, or snippets in 100% of privacy tests.
- **SC-010**: 100% of scope-boundary tests confirm this phase does not capture camera frames, run OCR, process images, clean OCR text, perform translation itself, synthesize new speech behavior, or orchestrate the full assistant workflow.
- **SC-011**: 100% of help command test phrases return supported command examples and trigger no reading, translation, capture, OCR, or cleanup action.
- **SC-012**: 100% of command-state tests show raw speech and recognized phrase text are discarded after classification and only latest safe command metadata is retained.

## Assumptions

- Phase 8 receives speech input or transcript-like command text from a recognition boundary or tests; it does not implement the complete audio loop.
- Phase 8 controls only a fixed set of commands for reading, translation, repeat sentence, repeat paragraph, stop, continue, and help.
- Phase 8 may route recognized commands to existing reading and translation behavior, but it does not implement new reading or translation behavior.
- Capture workflow commands and full end-to-end assistant orchestration are deferred to the later full workflow integration phase.
- Online speech recognition, if configured later, is optional and replaceable; local fixed-command recognition remains the required fallback when online recognition is disabled, unavailable, failed, or returns no supported command.
- Arabic and English command variants are deterministic and curated for assistive reliability.
- Spoken feedback is represented as guidance text in this phase and can be sent to the existing reading layer by later orchestration.
- Normal command state keeps only latest safe command metadata and does not persist command history, raw speech, or recognized phrase text.
