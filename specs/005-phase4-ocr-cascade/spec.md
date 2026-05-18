# Feature Specification: Phase 4 OCR Cascade Controller

**Feature Branch**: `005-phase4-ocr-cascade`

**Created**: 2026-05-17

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 4 with best practices"

## Clarifications

### Session 2026-05-17

- Q: What OCR quality score is good enough to accept? -> A: Accept OCR quality scores of 0.70 or higher; results below 0.70 are weak and trigger fallback or final failure.
- Q: What happens when the selected image is already marked unacceptable by image quality checks? -> A: Do not run OCR; return IMAGE_NOT_READY_FOR_OCR with recapture guidance.
- Q: How should online OCR availability and retries behave by default? -> A: Use one short availability check and at most one attempt per engine per cascade request; timeout or failure routes to the next allowed fallback.
- Q: How should High Accuracy Mode resolve similar acceptable scores? -> A: If acceptable scores differ by less than 0.05, prefer the local accuracy result, then use shorter duration as the final tie-breaker.
- Q: When may OCR text be written to logs? -> A: Only when both debug mode and explicit sensitive-text logging are enabled; default logs never include OCR text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the Best OCR Result Through Fallback (Priority: P1)

As a blind user, I need the assistant to accept a readable OCR result when the
first available OCR attempt is good, and automatically try the next free fallback
when the result is weak or fails, so that I hear reliable text instead of a
silent failure or poor reading.

**Why this priority**: OCR cascade routing is the main Phase 4 value. It
directly supports accuracy before speed and makes the previous OCR engines usable
as one reliable reading decision.

**Independent Test**: Given mocked OCR engine outcomes for success, weak text,
empty text, and engine failure, the cascade accepts the first good result,
falls back when needed, records the attempted path, and returns a structured
failure only after all allowed engines fail or produce unacceptable text.

**Acceptance Scenarios**:

1. **Given** the online primary OCR result is good, **When** normal OCR runs,
   **Then** the result is accepted and no fallback OCR engine is attempted.
2. **Given** the online primary OCR result is weak or empty, **When** normal OCR
   runs, **Then** the local accuracy fallback is attempted.
3. **Given** the local accuracy fallback also fails or is weak, **When** normal
   OCR runs, **Then** the emergency OCR fallback is attempted.
4. **Given** all allowed OCR engines fail or produce unacceptable text, **When**
   the cascade finishes, **Then** it returns a structured failure with guidance
   suitable for later spoken feedback.

---

### User Story 2 - Continue Reading When Internet Is Unavailable (Priority: P2)

As a blind user in an intermittent-network setting, I need OCR to skip online
OCR when internet is unavailable and use local fallbacks directly so that the
assistant can still attempt to read text offline.

**Why this priority**: Offline degraded mode is required by the constitution and
the Raspberry Pi target. Users should not wait for a known-unavailable online
path when local options can proceed.

**Independent Test**: Given online access is unavailable or online OCR is
disabled, the cascade skips online OCR, runs the local accuracy fallback first,
then the emergency fallback when needed, and records that offline routing was
used.

**Acceptance Scenarios**:

1. **Given** internet is unavailable, **When** normal OCR runs, **Then** the
   online OCR attempt is skipped and the local accuracy fallback is attempted
   first.
2. **Given** online OCR is disabled by request or configuration, **When** OCR
   runs, **Then** no user image is uploaded and local OCR attempts are used.
3. **Given** local accuracy OCR fails offline, **When** the cascade continues,
   **Then** emergency OCR is attempted before returning a final failure.

---

### User Story 3 - Compare Results in High Accuracy Mode (Priority: P3)

As a blind user who asks for higher accuracy, I need the assistant to compare
the strongest available OCR results instead of accepting the first result too
early, so that difficult documents have a better chance of being read correctly.

**Why this priority**: High Accuracy Mode improves difficult reads but can take
longer. It is valuable after the normal cascade and offline routing are reliable.

**Independent Test**: Given high accuracy mode is requested, the cascade compares
available online and local accuracy results, accepts the higher-quality result,
and attempts emergency OCR only when both primary candidates fail or are weak.

**Acceptance Scenarios**:

1. **Given** high accuracy mode is requested and online OCR is available,
   **When** OCR runs, **Then** the online and local accuracy results are compared
   before selecting the best acceptable result.
2. **Given** one high accuracy candidate is good and the other is weak,
   **When** comparison completes, **Then** the good result is selected with a
   score explanation.
3. **Given** both high accuracy candidates fail or are weak, **When** the
   cascade continues, **Then** emergency OCR is attempted before final failure.

---

### User Story 4 - Explain OCR Decisions Safely (Priority: P4)

As a developer or future assistant workflow, I need OCR cascade results to
include safe metadata, selected-engine decisions, fallback path, duration, and
failure reasons so that user-facing speech and troubleshooting can explain what
happened without exposing private document text by default.

**Why this priority**: Observability and privacy are both required. The cascade
must be debuggable without logging sensitive images or OCR text by default.

**Independent Test**: Given successful, fallback, offline, high-accuracy, and
failure scenarios, the cascade returns safe metadata and logs only selected
engine, attempt order, quality status, duration, fallback use, and failure codes,
while excluding raw OCR text unless explicit debug text logging is enabled.

**Acceptance Scenarios**:

1. **Given** a fallback path is used, **When** the cascade returns, **Then** the
   result includes the attempted engine path and selected engine.
2. **Given** OCR text contains private content, **When** default logging occurs,
   **Then** raw OCR text is not written to logs.
3. **Given** the cascade fails, **When** the failure is reported, **Then** it
   includes a stable failure reason and guidance suitable for later spoken
   feedback.

---

### Edge Cases

- Online OCR is disabled, not configured, times out, returns an error, or returns
  an unreadable response.
- Internet availability changes between the start of the OCR request and an
  online OCR attempt.
- The selected best frame is missing, invalid, or already rejected by image
  quality checks before OCR; the cascade does not run OCR and returns
  image-not-ready guidance.
- Online availability check succeeds but the online OCR attempt times out; the
  cascade records the timeout and attempts the next allowed fallback.
- OCR output is empty, extremely short, mostly symbols, repeated characters,
  fragmented Arabic, excessive spacing, or inconsistent with likely text area.
- The local accuracy engine is unavailable, fails to load, exceeds resource
  limits, or returns weak text.
- The emergency OCR engine is not installed, missing Arabic/English data, or
  returns weak text.
- High Accuracy Mode is requested while offline; online comparison is skipped
  and local candidates are used.
- Multiple acceptable OCR results have similar scores and require deterministic
  selection; High Accuracy Mode prefers the local accuracy result when scores
  differ by less than 0.05.
- All engines fail or are weak; the result must include actionable recapture or
  retry guidance instead of silent failure.
- Default logging must not include raw OCR text, clean text, image contents, or
  uploaded image payloads. OCR text may be logged only when both debug mode and
  explicit sensitive-text logging are enabled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single OCR cascade decision outcome for
  a selected image and language hints.
- **FR-002**: The system MUST evaluate OCR result quality before accepting a
  result, accepting scores of 0.70 or higher and treating scores below 0.70 as
  weak.
- **FR-003**: The system MUST accept a good online primary OCR result in normal
  online mode without attempting unnecessary fallback engines.
- **FR-004**: The system MUST attempt the local accuracy fallback when the online
  primary OCR result fails, is unavailable, or is weak.
- **FR-005**: The system MUST attempt the emergency OCR fallback when the local
  accuracy fallback fails, is unavailable, or is weak.
- **FR-006**: The system MUST skip online OCR when internet is unavailable,
  online OCR is disabled, or online use is not allowed for the request.
- **FR-007**: In offline routing, the system MUST attempt local accuracy OCR
  before emergency OCR.
- **FR-008**: In High Accuracy Mode, the system MUST compare available online
  primary and local accuracy results and select the better acceptable result.
- **FR-009**: In High Accuracy Mode, the system MUST attempt emergency OCR only
  if the compared primary candidates fail or are not acceptable.
- **FR-010**: The system MUST return structured final failure when all allowed
  OCR options fail or produce unacceptable text.
- **FR-011**: The system MUST include the attempted engine path, selected engine,
  fallback-used status, quality score, duration summary, and stable failure
  reason when available.
- **FR-012**: OCR quality scoring MUST detect empty text, very short text, high
  symbol noise, excessive spacing, repeated characters, and severe Arabic
  fragmentation.
- **FR-013**: OCR quality scoring MUST support Arabic, English, and mixed
  Arabic-English text without rejecting valid mixed-language output.
- **FR-014**: Similar acceptable OCR results MUST be resolved deterministically:
  normal mode uses quality score, preferred cascade order, and fastest
  successful result as the final tie-breaker; High Accuracy Mode prefers the
  local accuracy result when acceptable scores differ by less than 0.05, then
  uses fastest successful result as the final tie-breaker.
- **FR-015**: Expected OCR cascade failures MUST use stable error codes and
  human-readable messages suitable for later spoken feedback.
- **FR-016**: Default logs MUST include safe operational metadata only and MUST
  NOT include raw OCR text, clean text, image contents, uploaded payloads,
  secrets, or permanent debug paths.
- **FR-017**: Raw OCR text MAY be exposed to later text cleanup phases through
  structured results, but MUST NOT be logged by default.
- **FR-018**: Phase 4 MUST NOT implement camera capture, best-frame selection,
  text cleanup, voice command recognition, TTS playback, translation, or the
  full assistant workflow.
- **FR-019**: If the selected image is already marked unacceptable by image
  quality checks, the system MUST return `IMAGE_NOT_READY_FOR_OCR` with
  recapture guidance and MUST NOT run OCR engines.
- **FR-020**: The system MUST use one short online availability check before
  online OCR and MUST route to the next allowed fallback when the check fails or
  times out.
- **FR-021**: By default, the system MUST attempt each allowed OCR engine at
  most once per cascade request.
- **FR-022**: OCR text MAY be written to logs only when both debug mode and
  explicit sensitive-text logging are enabled.

### Constitution Requirements

- **CR-001**: Phase 4 MUST support accessibility-first behavior by returning OCR
  progress, fallback, success, and failure messages that can later be spoken.
- **CR-002**: Phase 4 MUST enforce accuracy-before-speed by rejecting weak OCR
  results and falling back before final failure.
- **CR-003**: Phase 4 MUST preserve free-only operation by requiring no paid OCR
  service and by keeping online OCR optional and replaceable.
- **CR-004**: Phase 4 MUST preserve offline degraded mode by attempting local OCR
  when online OCR is unavailable or disabled.
- **CR-005**: Phase 4 MUST preserve privacy by sending at most the selected best
  frame to the online OCR provider when online OCR is intentionally allowed, and
  by excluding OCR text from default logs.
- **CR-006**: Phase 4 MUST remain modular by keeping OCR cascade decisions
  independent from camera capture, text cleanup, speaking, translation, and full
  assistant orchestration.
- **CR-007**: Phase 4 MUST remain Raspberry Pi aware by avoiding default
  parallel execution of all OCR engines and by respecting bounded timeouts and
  lazy-loading assumptions.

### Key Entities *(include if feature involves data)*

- **OCR Cascade Request**: The selected image plus language hints, online/offline
  permissions, high-accuracy preference, image-readiness status, retry limits,
  and quality thresholds.
- **OCR Attempt**: One OCR engine attempt with engine name, success status,
  duration, raw result reference, quality score, and failure reason.
- **OCR Quality Report**: A deterministic assessment of extracted text quality,
  including acceptability, score, detected issues, guidance category, and
  whether the score is at or above the 0.70 acceptance threshold.
- **OCR Cascade Result**: The final accepted result or structured failure,
  including selected engine, attempt path, fallback-used status, quality summary,
  and safe metadata.
- **OCR Cascade Error**: Stable failure classification for unavailable online
  OCR, weak OCR result, local engine unavailable, emergency OCR unavailable, no
  text detected, image not ready for OCR, all engines failed, and unexpected
  cascade failure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In deterministic normal-mode tests, a good online primary OCR
  result is accepted without fallback in 100% of runs.
- **SC-002**: In deterministic weak-online tests, fallback to local accuracy OCR
  occurs in 100% of runs.
- **SC-003**: In deterministic weak-online and weak-local tests, emergency OCR is
  attempted in 100% of runs.
- **SC-004**: In offline-mode tests, online OCR is skipped in 100% of runs and
  local accuracy OCR is attempted first.
- **SC-005**: In High Accuracy Mode comparison tests, the higher-quality
  acceptable result is selected in 100% of runs.
- **SC-006**: OCR quality tests classify empty, very short, symbol-heavy,
  repeated-character, excessive-spacing, Arabic, English, and mixed-language
  cases with expected accept/reject outcomes.
- **SC-007**: All final failure tests return a stable error code and actionable
  guidance.
- **SC-008**: Default logging validation confirms 100% of logs exclude raw OCR
  text, clean text, image contents, uploaded payloads, secrets, and permanent
  debug paths.
- **SC-009**: Phase 4 validation confirms no camera capture, best-frame
  selection, text cleanup, voice command, TTS, translation, or full assistant
  workflow behavior is implemented.
- **SC-010**: Cascade routing tests are deterministic across repeated runs with
  the same mocked OCR outcomes.
- **SC-011**: OCR quality threshold tests accept scores of 0.70 or higher and
  trigger fallback or failure below 0.70 in 100% of deterministic cases.
- **SC-012**: Image-not-ready tests confirm OCR engines are not called in 100%
  of cases where pre-OCR image quality is already unacceptable.
- **SC-013**: Online availability and retry tests confirm no engine is attempted
  more than once per cascade request by default.
- **SC-014**: Sensitive text logging tests confirm OCR text appears in logs only
  when both debug mode and explicit sensitive-text logging are enabled.

## Assumptions

- Phase 4 consumes a selected image from previous phases but does not capture
  images or choose frames.
- The online primary OCR path is optional and may be skipped when unavailable,
  disabled, or disallowed by request.
- Local accuracy OCR is the preferred offline fallback, and emergency OCR is the
  final fallback.
- High Accuracy Mode may take longer than normal mode and is used only when
  explicitly requested.
- OCR quality thresholds are deterministic, with a default acceptance threshold
  of 0.70 that prefers fallback over weak reading.
- Raw OCR text is returned only through structured results for later cleanup and
  reading phases; default logs remain metadata-only.
- Online OCR availability checks are short and conservative; timeout is treated
  as unavailable for the current cascade request.
