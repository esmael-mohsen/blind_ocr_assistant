# Phase 9 Research: Full Assistive Workflow Integration

## Decision: Use a thin main entrypoint with an assistant workflow coordinator

**Rationale**: Phase 9 needs to connect many existing modules without moving
engine-specific behavior into the runtime entrypoint. A thin `main.py` can wire
configuration, logging, signal handling, and dependencies, while
`modules.assistant.workflow` owns the command-to-workflow orchestration.

**Alternatives considered**:
- Put orchestration directly in `main.py`: rejected because it makes tests
  harder and couples runtime setup to workflow decisions.
- Extend `DialogueManager` into the full workflow coordinator: rejected because
  Phase 8 dialogue routing is intentionally scoped to command recognition and
  narrow reading/translation handoffs.

## Decision: Keep one active read workflow at a time

**Rationale**: A single Raspberry Pi camera and OCR cascade should not process
multiple capture/OCR runs concurrently. Rejecting additional read commands with
spoken busy guidance reduces resource pressure and avoids stale state races.

**Alternatives considered**:
- Queue read commands: rejected because blind users need immediate feedback and
  queued captures can become stale.
- Cancel current read automatically: rejected because it could discard a valid
  in-progress capture or OCR result without clear user intent.

## Decision: End all-frame-rejected capture attempts instead of auto-looping

**Rationale**: The constitution requires bounded capture and recoverable
guidance. If every frame in a burst fails quality checks, the assistant should
explain the issue and wait for an explicit retry/read command.

**Alternatives considered**:
- Auto-repeat capture until success: rejected because it can trap the device in
  a noisy loop and drain Raspberry Pi resources.
- Send rejected frames to OCR anyway: rejected because accuracy before speed
  requires preventing bad images from reaching OCR whenever possible.

## Decision: Preserve latest successful text state across failed attempts

**Rationale**: A failed later capture or OCR attempt should not erase the last
usable clean text. Preserving latest clean text and translation supports
translation, repeat, and recovery after transient failures.

**Alternatives considered**:
- Clear text state at the start of every read attempt: rejected because it makes
  transient camera/OCR errors destructive.
- Persist text history to disk: rejected because Phase 9 only needs latest
  in-memory state and privacy by default discourages unnecessary retention.

## Decision: Treat configured component timeouts as recoverable failures

**Rationale**: Camera, OCR, translation, and speech boundaries may be slow or
unavailable on Raspberry Pi. The coordinator should convert timeouts into
structured failures with spoken guidance while preserving safe state.

**Alternatives considered**:
- Let timeout exceptions bubble up: rejected because user-facing workflows must
  not crash silently.
- Retry internally without user input: rejected because bounded attempts and
  clear recovery guidance are safer for assistive use.

## Decision: Use safe metadata-only observability

**Rationale**: Full workflow integration is where images, OCR text,
translations, command results, and speech status meet. Logs need workflow
visibility without content exposure: statuses, selected engines, fallback use,
durations, and error categories are enough for normal diagnostics.

**Alternatives considered**:
- Log raw text snippets for easier debugging: rejected for default behavior
  because sensitive real-world text may be captured.
- Disable logs for privacy: rejected because safe operational metadata is
  needed to diagnose hardware and fallback behavior.

## Decision: Shutdown is operational lifecycle, not a new voice command

**Rationale**: Phase 8 already treats stop as playback control. Phase 9 should
handle process interruption, service stop, and test harness shutdown cleanly
without expanding the fixed command catalog.

**Alternatives considered**:
- Add a new spoken exit command: rejected because Phase 9 scope excludes new
  command categories.
- Reuse stop as shutdown: rejected because users need stop to remain a reading
  playback control.
