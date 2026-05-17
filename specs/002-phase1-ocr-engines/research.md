# Research: Phase 1 OCR Engine Prototype

## Decision: Use a shared OCR interface for all engines

**Rationale**: The later cascade must treat online, local accuracy, and emergency
engines consistently. A shared interface keeps engine-specific details isolated
and makes success/failure handling testable before cascade logic exists.

**Alternatives considered**:
- Let each engine expose its own method shape: rejected because it would make
  cascade orchestration brittle.
- Build the cascade first: rejected because Phase 1 must validate engines
  independently.

## Decision: Represent OCR input and output with explicit request/result models

**Rationale**: OCR requests need language hints, mode, optional preprocessing
variant, and online/offline permissions. OCR results need engine name, raw text,
duration, success, confidence/quality placeholders, fallback flag, and stable
failure details.

**Alternatives considered**:
- Return raw strings: rejected because empty text, weak output, timing, and
  engine failures would be ambiguous.
- Reuse generic result only: rejected because OCR needs domain-specific metadata.

## Decision: Make live online OCR tests opt-in

**Rationale**: The project must run local tests without internet or free online
credentials. Mocked provider tests cover request/response behavior; live tests
can be enabled only when credentials are available.

**Alternatives considered**:
- Require live online OCR in every test run: rejected because it breaks offline
  development and CI.
- Exclude live tests entirely: rejected because maintainers still need a clear
  manual path to verify the free online provider.

## Decision: Use configurable timeout plus one retry for transient online failure

**Rationale**: A single retry handles common transient network/provider failures
without turning Phase 1 into complex resiliency logic. Timeouts prevent blocking
the assistant indefinitely.

**Alternatives considered**:
- No retry: rejected because temporary provider issues are common.
- Multiple retries with backoff: deferred to later operational hardening because
  Phase 1 only validates engine prototypes.

## Decision: Lazy-load the local accuracy OCR engine

**Rationale**: Local accuracy OCR can be memory-heavy on Raspberry Pi 4. It must
not load during import, bootstrap help, or unrelated engine tests.

**Alternatives considered**:
- Load the model in the constructor or module import: rejected because it risks
  high memory use and slow startup.
- Require all machines to install the model before tests: rejected because local
  availability varies.

## Decision: Treat empty and weak OCR output as failure

**Rationale**: Blind users cannot visually verify output. Empty or obviously
weak text should be classified as `NO_TEXT_DETECTED` or `WEAK_OCR_RESULT`, not
successful OCR.

**Alternatives considered**:
- Return success with empty raw text: rejected because downstream reading could
  silently mislead users.
- Fully score OCR quality in Phase 1: deferred to the later OCR quality and
  cascade phases.

## Decision: Log metadata only by default

**Rationale**: OCR text can contain sensitive user content. Phase 1 logs should
include engine name, duration, status, and error codes while excluding raw OCR
text unless an explicit debug setting is enabled later.

**Alternatives considered**:
- Log raw OCR text for easier debugging: rejected by privacy-by-default
  governance.
- Disable all logging: rejected because failure diagnosis needs safe metadata.
