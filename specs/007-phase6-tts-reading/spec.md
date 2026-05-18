# Feature Specification: Phase 6 TTS Reading Controller

**Feature Branch**: `007-phase6-tts-reading`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 6 with best practices"

## Clarifications

### Session 2026-05-18

- Q: How should pause behave when native pause/resume is unavailable? -> A: Stop speech safely, keep the current segment as the resume point, and continue by replaying that segment with clear guidance.
- Q: What speech-rate bounds should tests use? -> A: Default rate is 150 words per minute, with accepted rates clamped to 80-220 words per minute.
- Q: How should text be segmented for repeat behavior? -> A: Paragraphs are separated by blank lines; sentences are split on Arabic and English sentence-ending punctuation while preserving logical order.
- Q: What counts as the last repeatable sentence or paragraph? -> A: The last successfully requested segment is repeatable; if progress is unknown, repeat the current segment rather than guessing ahead.
- Q: How should TTS failures affect reading state? -> A: Failed speech leaves reading inactive, preserves the last successful repeat history, and returns structured guidance without exposing text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hear Clean OCR Text Read Aloud (Priority: P1)

As a blind user, I need the assistant to read the latest clean OCR text aloud in Arabic or English so I can consume the captured content without looking at a screen.

**Why this priority**: Reading clean OCR text aloud is the central value of the assistant after OCR and cleanup are available.

**Independent Test**: Provide clean Arabic and English text to the reading controller with a mocked speech engine; verify reading starts, the correct text is sent to speech, reading state is updated, and user-safe status guidance is returned.

**Acceptance Scenarios**:

1. **Given** clean Arabic text is available, **When** reading starts, **Then** the assistant sends the Arabic text to speech and reports that reading has started.
2. **Given** clean English text is available, **When** reading starts, **Then** the assistant sends the English text to speech and reports that reading has started.
3. **Given** no clean text is available, **When** reading is requested, **Then** the assistant does not speak empty content and returns guidance that no readable text is available.

---

### User Story 2 - Control Playback Without Visual Feedback (Priority: P2)

As a blind user, I need to stop, pause when available, continue, and adjust reading speed so I can control long readings by voice or later command routing.

**Why this priority**: Long OCR results must be controllable. Without stop and rate control, the assistant can become disruptive or unusable.

**Independent Test**: Use a mocked speech engine and active reading state; verify stop, pause, continue, and rate changes update state and return spoken guidance without needing visual confirmation.

**Acceptance Scenarios**:

1. **Given** reading is active, **When** the user stops reading, **Then** speech stops and the state records that reading is no longer active.
2. **Given** reading is active and pause is supported, **When** the user pauses, **Then** speech pauses and the state records a paused state.
3. **Given** reading is paused, **When** the user continues, **Then** speech resumes from the current segment or replays that segment with clear guidance when native resume is unavailable.
4. **Given** the user changes reading speed, **When** future speech is started, **Then** the configured rate is clamped between 80 and 220 words per minute.

---

### User Story 3 - Repeat Recent Text Segments (Priority: P3)

As a blind user, I need to repeat the last sentence or paragraph so I can re-hear important information without restarting the whole reading.

**Why this priority**: Repetition makes the assistant practical for receipts, medicine instructions, forms, and long paragraphs where a user may miss details.

**Independent Test**: Provide segmented text with several sentences and paragraphs; verify the controller tracks the last spoken segment and can repeat the last sentence and last paragraph through the speech engine.

**Acceptance Scenarios**:

1. **Given** a sentence has been successfully requested for speech, **When** repeat last sentence is requested, **Then** only that sentence is spoken again.
2. **Given** a paragraph has been successfully requested for speech, **When** repeat last paragraph is requested, **Then** that paragraph is spoken again.
3. **Given** no previous sentence or paragraph exists, **When** repeat is requested, **Then** the assistant returns guidance that there is nothing to repeat.

### Edge Cases

- Empty, whitespace-only, or cleanup-failed text must not be spoken and must return clear guidance.
- Very short text must still be spoken as a complete reading.
- Arabic, English, and mixed text must preserve logical reading order from Phase 5.
- Unsupported, missing, or unavailable TTS engine behavior must return structured failure and guidance instead of crashing.
- Stop must be safe to call when no reading is active.
- Pause and continue must degrade gracefully when the speech engine does not support native pause/resume by stopping safely and replaying the current segment on continue.
- Speech rate must default to 150 words per minute and must be clamped to 80-220 words per minute.
- Sentence segmentation must support Arabic and English sentence-ending punctuation, and paragraph segmentation must use blank-line boundaries.
- If speech progress is unknown, repeat operations must use the last successfully requested segment rather than guessing a later segment.
- TTS failures must leave reading inactive, preserve the last successful repeat history, and return structured guidance without exposing text.
- Repeating a sentence or paragraph must not expose raw OCR text if only clean text was approved for reading.
- Default logs must not include clean text, raw text, or spoken text snippets.
- This phase must not capture camera frames, run OCR, clean text, translate text, parse voice commands, or orchestrate the full assistant workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept clean text prepared by prior phases and start reading it aloud.
- **FR-002**: System MUST support Arabic and English reading requests.
- **FR-003**: System MUST return structured success or failure results for read, stop, pause, continue, rate change, and repeat operations.
- **FR-004**: System MUST avoid speaking empty or whitespace-only text and MUST return guidance when no readable text is available.
- **FR-005**: System MUST maintain reading state including active, paused, current text identity, last sentence, last paragraph, and configured rate.
- **FR-006**: System MUST provide stop control that is safe whether or not reading is active.
- **FR-007**: System MUST provide pause and continue controls when supported and graceful guidance when native pause/resume is unavailable.
- **FR-008**: System MUST support configurable speech rate with a default of 150 words per minute and clamp accepted rates to 80-220 words per minute.
- **FR-009**: System MUST segment clean text into sentences using Arabic and English sentence-ending punctuation and into paragraphs using blank-line boundaries.
- **FR-010**: System MUST repeat the last sentence when one exists.
- **FR-011**: System MUST repeat the last paragraph when one exists.
- **FR-012**: System MUST return guidance when repeat is requested before any sentence or paragraph has been read.
- **FR-013**: System MUST expose a speech engine boundary so the reading controller can be tested with a mock engine and later use the selected free local speech engine.
- **FR-014**: System MUST return structured failures for missing, unavailable, or failing speech engines without crashing.
- **FR-015**: System MUST preserve Phase 5 clean-text logical order for Arabic, English, and mixed text.
- **FR-016**: System MUST exclude raw text, clean text, and spoken snippets from default logs.
- **FR-017**: System MUST keep this phase scoped to TTS reading, playback control, text segmentation, repeat behavior, and reading state only.
- **FR-018**: System MUST treat the last successfully requested sentence or paragraph as repeatable history, and MUST replay the current segment on continue when native resume is unavailable.
- **FR-019**: System MUST leave reading inactive after TTS failure while preserving the last successful repeat history.

### Constitution Requirements

- **CR-001**: Feature MUST be usable without visual confirmation and MUST define spoken feedback for reading start, stop, pause, continue, rate changes, repeat success, repeat failure, empty text, and TTS failure.
- **CR-002**: Feature MUST document TTS fallback behavior and unavailable-engine behavior because it touches TTS workflow.
- **CR-003**: Feature MUST avoid paid-service dependency; the initial TTS path must use free local speech behavior.
- **CR-004**: Feature MUST define privacy behavior for clean text, raw text, spoken text, logs, and debug artifacts.
- **CR-005**: Feature MUST define measurable acceptance criteria for Arabic reading, English reading, mixed text handling, playback control, repeat behavior, and TTS failure modes.

### Key Entities *(include if feature involves data)*

- **SpeechRequest**: Represents text to speak, language, rate, operation context, and segment identity.
- **SpeechResult**: Represents speech success or failure, duration if available, engine name, and user-safe guidance.
- **ReadingState**: Represents whether reading is active or paused, the current clean text, current segment, current rate, last successfully requested sentence, last successfully requested paragraph, and last operation.
- **TextSegment**: Represents a sentence or paragraph prepared for reading or repeat, including segment type, order, and text content.
- **ReadingControlCommand**: Represents stop, pause, continue, rate change, repeat sentence, or repeat paragraph requests.
- **TTSError**: Represents stable TTS failure categories and guidance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Arabic and English reading tests send the expected clean text to the speech engine.
- **SC-002**: 100% of empty or whitespace-only reading requests return guidance and do not call the speech engine.
- **SC-003**: 100% of stop requests leave reading state inactive, including when no reading was active.
- **SC-004**: 100% of supported pause and continue scenarios update reading state and return guidance.
- **SC-005**: 100% of speech rate changes use the 150 words-per-minute default and clamp requested rates to 80-220 words per minute.
- **SC-006**: Sentence and paragraph segmentation supports repeat behavior correctly for at least 95% of deterministic Arabic, English, and mixed fixture samples.
- **SC-007**: 100% of repeat requests with available history speak only the last successfully requested sentence or paragraph.
- **SC-008**: 100% of repeat requests without history return guidance and do not speak unrelated text.
- **SC-009**: 100% of TTS engine failures return structured failure and user-safe guidance without uncaught exceptions.
- **SC-010**: Default logs contain no raw text, clean text, or spoken text snippets in 100% of privacy tests.
- **SC-011**: 100% of continue requests without native resume replay the current segment and return guidance explaining the fallback.
- **SC-012**: 100% of TTS failure tests leave reading inactive and preserve prior successful repeat history.

## Assumptions

- Phase 6 receives clean text and language/direction metadata from Phase 5 or equivalent tests; it does not perform OCR or cleanup itself.
- The initial speech engine is free and local; higher-quality voices may be added later without changing the reading controller contract.
- Pause/resume may not be natively supported by every speech engine, so the fallback is to stop safely and replay the current segment on continue.
- Mixed Arabic/English text is read in the logical order supplied by Phase 5.
- User-facing spoken feedback is represented as guidance text in this phase and can be routed to actual speech by the reading controller.
- Privacy defaults follow the existing project policy: text content is excluded from normal logs and any sensitive text logging requires explicit opt-in.
