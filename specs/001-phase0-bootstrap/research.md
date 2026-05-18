# Research: Phase 0 Repository Bootstrap

## Decision: Use Python 3.10+ with a minimal standard-library bootstrap

**Rationale**: The full assistant is planned for Python 3.10+ on Raspberry Pi.
Phase 0 should prove importability, configuration, logging, result handling, and
entrypoint behavior without installing heavy OCR, camera, voice, or translation
packages.

**Alternatives considered**:
- Add all future dependencies now: rejected because it would make bootstrap
  fragile on machines without Raspberry Pi hardware or OCR/audio packages.
- Use a different language for tooling: rejected because it would split the
  project foundation from the planned assistant runtime.

## Decision: Keep runtime dependencies light and make quality tools optional

**Rationale**: `pytest` is needed to prove the bootstrap. `ruff`, `black`, and
`mypy` are useful, but Phase 0 self-check should report their absence as
optional instead of failing core readiness.

**Alternatives considered**:
- Require all quality tools immediately: rejected because it can block first-run
  setup before the core scaffold is useful.
- Skip quality tooling entirely: rejected because later phases benefit from a
  known lint, format, and type-check path.

## Decision: Use local filesystem storage with safe automatic folder creation

**Rationale**: The initial project requires local logs and reserved runtime
directories, but no database. Creating `logs/`, `debug_captures/`,
`benchmark_results/`, and `config/` during setup/self-check reduces first-run
friction and keeps the system offline-capable.

**Alternatives considered**:
- Require manual folder creation: rejected because it adds avoidable setup
  failure points.
- Create cloud storage integration: rejected by the privacy and no-cloud default
  constraints.

## Decision: Define a shared Operation Result pattern in Phase 0

**Rationale**: Later engine phases need structured failures instead of uncaught
exceptions. A small result object with success status, optional value, optional
error code, and message establishes the cascade/error-handling convention early.

**Alternatives considered**:
- Let every module choose its own return shape: rejected because fallback logic
  would become inconsistent.
- Raise exceptions for expected failures: rejected because expected engine and
  environment failures must be speakable and testable.

## Decision: Expose help and bootstrap self-check from the entrypoint

**Rationale**: The accepted spec requires a visible way to prove repository
readiness without invoking OCR, camera, audio, translation, internet, or paid
services. A self-check can validate imports, config defaults, local folders, and
optional tooling status.

**Alternatives considered**:
- Only provide `--help`: rejected because help alone does not prove local
  readiness.
- Start the assistant loop in Phase 0: rejected because that belongs to later
  voice and workflow phases.
