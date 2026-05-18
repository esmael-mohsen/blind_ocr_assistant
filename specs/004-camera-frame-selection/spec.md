# Feature Specification: Phase 3 Camera Integration and Best Frame Selection

**Feature Branch**: `004-camera-frame-selection`

**Created**: 2026-05-17

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 3 with best practices"

## Clarifications

### Session 2026-05-17

- Q: How should out-of-range burst counts be handled? -> A: Clamp capture count to the 10-20 frame range.
- Q: What camera source order should Phase 3 use? -> A: Prefer the target depth camera, then fall back to generic RGB capture.
- Q: What happens if capture times out before the requested burst count? -> A: Score any valid captured frames; fail only when no valid frames were captured.
- Q: How should similar frame scores be resolved? -> A: Prefer acceptable image quality first, then stability, then earliest frame.
- Q: What default distance categories should depth guidance use? -> A: Too close under 25 cm, acceptable 25-75 cm, too far above 75 cm.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select the Best Frame From a Capture Burst (Priority: P1)

As a blind user, I need the assistant to evaluate a short burst of camera frames
and choose the clearest one so that later OCR receives the most readable image
instead of an arbitrary frame.

**Why this priority**: Best-frame selection is the main Phase 3 value. It
directly supports accuracy before speed and can be tested with deterministic
frame fixtures even when camera hardware is unavailable.

**Independent Test**: Given a bounded set of candidate frames with varied
sharpness, brightness, contrast, text presence, and stability, the selector
chooses the highest-quality frame, returns its score breakdown, and provides
guidance when no frame is acceptable.

**Acceptance Scenarios**:

1. **Given** a burst containing one clearly sharp, readable frame and several
   poorer frames, **When** best-frame selection runs, **Then** the clearest frame
   is selected with a score breakdown.
2. **Given** all frames in a burst are dark, blurry, or unlikely to contain text,
   **When** best-frame selection runs, **Then** no frame is accepted and the
   result includes corrective guidance for recapture.
3. **Given** two frames have similar quality, **When** best-frame selection runs,
   **Then** the decision is deterministic and stable across repeated runs.
4. **Given** the configured capture count is outside the allowed range, **When**
   a burst request is created, **Then** the request is clamped to the bounded
   range before capture starts.

---

### User Story 2 - Capture RGB Frames and Release Camera Resources (Priority: P2)

As a developer or hardware tester, I need a camera abstraction that can capture
RGB frames from the target camera or a safe fallback so that later workflow
phases can request still frames without owning camera-specific details.

**Why this priority**: Reliable capture and cleanup are required before the full
assistant can use real images. It must degrade cleanly on development machines
without hardware.

**Independent Test**: With a mocked camera source, the capture layer prefers the
target depth camera path when available, falls back to generic RGB capture when
the target path is unavailable, captures one or more RGB frames, returns
structured frame candidates, and releases resources after success, failure, and
timeout paths. With hardware available, an opt-in manual script verifies live
RGB capture.

**Acceptance Scenarios**:

1. **Given** a working camera source, **When** a single RGB capture is requested,
   **Then** the result contains one valid frame candidate and camera metadata.
2. **Given** capture completes or fails, **When** the operation exits, **Then**
   camera resources are released exactly once.
3. **Given** camera hardware is not available, **When** local automated tests
   run, **Then** hardware-dependent checks are skipped or mocked without failing
   local validation.
4. **Given** a capture timeout or unreadable frame, **When** capture fails,
   **Then** the result contains a stable failure reason and user-safe guidance.
5. **Given** capture times out after at least one valid frame is captured,
   **When** selection runs, **Then** the valid captured frames are still scored
   and the timeout condition is recorded.

---

### User Story 3 - Use Depth for Distance Guidance When Available (Priority: P3)

As a blind user, I need the assistant to use depth information when available to
tell me whether the document is too close or too far, while still working in
RGB-only mode when depth is unavailable.

**Why this priority**: Depth guidance improves capture quality on the target
camera, but the system must remain useful when depth support is absent or
unsupported.

**Independent Test**: Given mocked RGB+depth candidates, the system classifies
distance as too close, acceptable, too far, or unavailable; given RGB-only
candidates, it still selects a best frame without failing.

**Acceptance Scenarios**:

1. **Given** a frame with usable depth data, **When** distance analysis runs,
   **Then** the result includes a distance status and guidance.
2. **Given** a frame is too close or too far, **When** the candidate is scored,
   **Then** distance reduces the score and the guidance asks the user to adjust
   camera distance.
3. **Given** depth data is unavailable, invalid, or unsupported, **When** frame
   selection runs, **Then** the system continues in RGB-only mode and records
   depth as unavailable.
4. **Given** depth data conflicts with otherwise strong RGB quality, **When**
   the frame is scored, **Then** the score remains deterministic and the
   distance warning is preserved.

---

### Edge Cases

- Target camera is disconnected, busy, unsupported, or fails to open.
- Camera opens but returns no frame, an empty frame, corrupted data, or frames
  with inconsistent dimensions.
- Capture times out before the requested burst count is reached; valid captured
  frames are still scored, while zero valid frames returns a capture failure.
- The requested burst count is below 10 or above 20 and is clamped before
  capture starts.
- All frames are poor quality or receive only uncertain quality reports.
- Frames have similar scores and require deterministic tie-breaking by
  acceptable quality first, then stability, then earliest frame.
- Depth data is missing, invalid, noisy, out of range, or not aligned with RGB.
- Depth data indicates a document closer than 25 cm, between 25-75 cm, or
  farther than 75 cm.
- The camera supports RGB but not depth; RGB-only mode must still work.
- Camera resources must be released after success, failure, timeout, or
  cancellation.
- Debug image saving is disabled by default; no captured frame is stored
  permanently unless explicit debug configuration enables it.
- Phase 3 runs on a development machine without camera hardware.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a camera abstraction that can capture RGB
  frame candidates without exposing hardware-specific behavior to later phases.
- **FR-002**: The system MUST prefer the target depth camera when available and
  MUST fall back to generic RGB capture when the target camera or depth support
  is unavailable.
- **FR-003**: The system MUST capture a bounded burst of frames, with the normal
  configured range limited to 10-20 frames; out-of-range requests MUST be
  clamped before capture starts.
- **FR-004**: Every captured frame candidate MUST include a stable identifier,
  RGB image data, timestamp, score fields, and safe metadata.
- **FR-005**: Frame candidates MAY include depth data and distance status when
  available.
- **FR-006**: The system MUST score frame candidates using image quality signals
  from Phase 2 plus stability and distance signals when available.
- **FR-007**: The system MUST select the highest-scoring acceptable frame from a
  burst and return the full score breakdown. Ties MUST prefer acceptable image
  quality first, then stability, then earliest frame order.
- **FR-008**: If no acceptable frame exists, the system MUST return a structured
  failure and actionable guidance for recapture.
- **FR-009**: Best-frame selection MUST be deterministic for the same ordered
  input frames and thresholds.
- **FR-010**: Camera resources MUST be released after every success, failure,
  timeout, or cancellation path.
- **FR-011**: Camera hardware tests MUST be opt-in or manual so local automated
  tests can pass without hardware.
- **FR-012**: Phase 3 MUST include a camera test script that reports camera
  availability, RGB capture status, optional depth status, selected-frame
  status, and resource cleanup status.
- **FR-013**: Expected capture, camera, depth, and frame-selection failures MUST
  use stable error codes and human-readable messages suitable for later spoken
  feedback.
- **FR-014**: Default logs MUST include safe metadata such as frame count,
  selected frame id, score summary, distance status, fallback mode, and failure
  code, but MUST NOT include image contents or permanent debug paths.
- **FR-015**: Phase 3 MUST NOT implement OCR engine execution, OCR cascade
  routing, text cleanup, voice command recognition, TTS playback, translation,
  or the full assistant workflow.
- **FR-016**: Permanent frame saving MUST be disabled by default and controlled
  only by explicit debug configuration when introduced.
- **FR-017**: If capture times out after one or more valid frames were captured,
  the system MUST still score those valid frames and record the timeout
  condition; if zero valid frames were captured, it MUST return a structured
  capture failure.
- **FR-018**: Depth guidance MUST classify distance as too close below 25 cm,
  acceptable from 25 cm through 75 cm, too far above 75 cm, or unavailable.

### Constitution Requirements

- **CR-001**: Phase 3 MUST support accessibility-first behavior by returning
  capture and recapture guidance that can later be spoken to a blind user.
- **CR-002**: Phase 3 MUST enforce accuracy-before-speed by selecting a best
  frame from a bounded burst rather than using an arbitrary frame.
- **CR-003**: Phase 3 MUST preserve free-only and offline-capable operation by
  requiring no paid service or mandatory cloud dependency.
- **CR-004**: Phase 3 MUST preserve graceful degradation by continuing in
  RGB-only mode when depth is unavailable and by returning structured failures
  when capture cannot proceed.
- **CR-005**: Phase 3 MUST define privacy behavior for captured frames, logs,
  and debug artifacts, with no permanent storage by default.
- **CR-006**: Phase 3 MUST remain modular by keeping camera capture and
  best-frame selection independent from OCR engines, command handling, speaking,
  translation, and full workflow orchestration.
- **CR-007**: Phase 3 MUST remain Raspberry Pi aware by bounding frame counts,
  timeouts, memory use, and resource lifetimes.

### Key Entities *(include if feature involves data)*

- **Camera Source**: A real or mocked source capable of producing RGB frames and
  optional depth data.
- **Capture Request**: A request for one RGB frame or a bounded burst, including
  capture count, timeout, and whether depth is requested.
- **Frame Candidate**: A captured or synthetic frame with id, RGB data,
  optional depth data, timestamp, quality score fields, distance status, total
  score, and safe metadata.
- **Depth Report**: Distance classification for a candidate, including status,
  score contribution, and guidance when depth is usable or unavailable. Default
  categories are too close below 25 cm, acceptable from 25 cm through 75 cm, too
  far above 75 cm, and unavailable.
- **Frame Score**: A deterministic score breakdown combining image quality,
  stability, distance, and acceptance status.
- **Best Frame Selection Result**: Structured outcome containing selected frame
  when available, all candidate score summaries, guidance, success status, and
  failure details.
- **Camera Error**: Stable failure classification for camera open failure,
  capture timeout, empty frame, invalid frame, depth unavailable, no acceptable
  frame, and unexpected capture failure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For deterministic burst fixtures with one clearly best frame, the
  selector chooses the expected frame in 100% of test runs.
- **SC-002**: For bursts containing only poor or uncertain frames, 100% of
  results return no selected frame and include actionable recapture guidance.
- **SC-003**: 100% of capture success, failure, and timeout tests verify camera
  resources are released.
- **SC-004**: Local automated tests pass without physical camera hardware by
  using mocked camera sources or skipped opt-in hardware checks.
- **SC-005**: RGB-only mode succeeds in frame selection when depth data is
  unavailable.
- **SC-006**: Depth-aware tests classify too-close, acceptable, too-far, and
  unavailable distance cases.
- **SC-007**: Default validation creates no permanent captured-frame artifacts
  unless debug image saving is explicitly enabled.
- **SC-008**: Phase 3 validation confirms no OCR execution, OCR cascade, text
  cleanup, voice command, TTS, translation, or full assistant workflow behavior
  is implemented.
- **SC-009**: 100% of tie-breaker tests select by acceptable quality first,
  stability second, and earliest frame third.
- **SC-010**: 100% of partial-timeout tests score valid captured frames when at
  least one valid frame exists and fail only when no valid frame exists.

## Assumptions

- Phase 3 consumes Phase 2 image-quality results and preprocessing readiness but
  does not run OCR.
- Live hardware checks are optional/manual; automated tests use mocked camera
  sources and deterministic frame fixtures. The target depth camera is preferred
  when available, with generic RGB capture as the degraded fallback.
- The normal burst count defaults to the project setting of 15 frames and is
  clamped to the 10-20 frame range for Phase 3 capture workflows.
- Depth data is treated as an enhancement, not a requirement; RGB-only capture
  must remain a valid degraded mode. Default depth categories are too close
  below 25 cm, acceptable from 25 cm through 75 cm, and too far above 75 cm.
- Camera test output may be textual for developers, while user-facing capture
  guidance is returned as messages that later TTS phases can speak.
- Captured frames are handled in memory by default; permanent saving is reserved
  for explicit debug configuration.
