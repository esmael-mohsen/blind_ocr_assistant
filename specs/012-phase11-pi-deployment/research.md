# Research: Phase 11 Raspberry Pi Deployment Hardening

## Decision: Use Four Canonical Readiness States

**Rationale**: Ready, Degraded, Blocked, and Manual Verification Needed provide
clear outcomes for blind-user startup, maintainer diagnostics, and automated
tests. They separate usable offline/RGB-only states from true blocking failures
and from hardware checks that cannot be proven automatically.

**Alternatives considered**:

- Boolean pass/fail only: rejected because it hides useful degraded operation.
- Many subsystem-specific states: rejected because it complicates spoken
  feedback and acceptance tests.

## Decision: Run Lightweight Startup Checks Automatically

**Rationale**: Every assistant start should verify configuration, local
folders, privacy settings, basic dependency availability, log readiness, and
safe environment conditions without eagerly loading heavy OCR models or
requiring camera/audio interaction.

**Alternatives considered**:

- Run full diagnostics at every startup: rejected because camera, microphone,
  speaker, and model loading checks can delay startup and create hardware side
  effects.
- Run no startup checks: rejected because deployment failures would remain
  silent until the user attempts reading.

## Decision: Provide Full Diagnostics As Explicit Maintainer Action

**Rationale**: Full diagnostics can safely validate camera capture, audio
output, command input, local OCR fallback loading, no-internet startup,
internet recovery, and shutdown behavior when a maintainer is present. This
keeps normal user startup fast while preserving release confidence.

**Alternatives considered**:

- Manual checklist only: rejected because many checks can be automated or
  mocked in tests.
- Always-on diagnostics loop: rejected because the assistant should not
  continuously probe hardware during normal use.

## Decision: Keep Service Startup Optional And Disabled By Default

**Rationale**: A disabled-by-default service template lets maintainers opt into
hands-free startup after hardware and privacy settings are validated. It avoids
surprising startup behavior on development machines and protects shared devices
from accidental microphone/camera use.

**Alternatives considered**:

- Enable service automatically during install: rejected because unattended
  startup should be a deliberate deployment choice.
- Omit service support: rejected because the target use case benefits from
  reliable device-style startup.

## Decision: Enforce 50 MB Default Normal Log Budget

**Rationale**: A small bounded budget protects Raspberry Pi storage during
long-running operation while still retaining useful local diagnostics. The
budget applies to normal logs, not private debug captures, and can be adjusted
later through explicit configuration if needed.

**Alternatives considered**:

- Unbounded logs: rejected because repeated use can fill storage.
- Very small budget below 10 MB: rejected because it can erase useful startup
  and failure history too aggressively.

## Decision: Privacy-Safe Validation Artifacts Only

**Rationale**: Deployment reports are useful for support and release checks,
but they must not expose user documents, camera images, OCR text,
translations, secrets, endpoint credentials, or private debug paths. Safe
summaries can include status, category, safe code, duration, and remediation.

**Alternatives considered**:

- Include raw logs and OCR samples in reports: rejected because deployment may
  involve private real-world text.
- Store no report at all: rejected because maintainers need local evidence for
  setup and troubleshooting.

## Decision: Validate Heavy Engines Without Import-Time Loading

**Rationale**: Raspberry Pi memory is constrained, and the existing
constitution requires lazy loading. Diagnostics should check configured
availability and optionally perform explicit load/run probes only in full
diagnostics, with clear timeouts and failure categories.

**Alternatives considered**:

- Load all local OCR engines during normal startup: rejected due memory and
  latency risk.
- Avoid local OCR validation entirely: rejected because offline readiness is a
  core deployment requirement.

## Decision: Document Manual Hardware Acceptance

**Rationale**: Some checks, especially microphone quality, speaker audibility,
service behavior after boot, and Orbbec depth behavior, require the real target
device. Documented manual acceptance keeps automated tests honest and prevents
false confidence from mocked development environments.

**Alternatives considered**:

- Treat mocked tests as full deployment proof: rejected because hardware
  behavior differs on Raspberry Pi.
- Require target hardware for all tests: rejected because it would block normal
  development and CI-style validation.
