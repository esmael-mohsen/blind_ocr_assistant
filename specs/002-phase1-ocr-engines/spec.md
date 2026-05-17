# Feature Specification: Phase 1 OCR Engine Prototype

**Feature Branch**: `002-phase1-ocr-engines`

**Created**: 2026-05-17

**Status**: Draft

**Input**: User description: "Read implementationPlan.md and create the specification for Phase 1 with best practices"

## Clarifications

### Session 2026-05-17

- Q: What sample inputs should Phase 1 require? -> A: Small local fixtures plus mockable image inputs.
- Q: How should live online OCR tests behave by default? -> A: Opt-in only; skipped without free credentials.
- Q: How should empty or weak OCR output be classified? -> A: Structured no-text or weak-result failure, not success.
- Q: What reliability limits should engine calls expose? -> A: Configurable timeout with one retry for transient online failures.
- Q: What OCR text may be logged by default? -> A: Metadata only; raw OCR text excluded unless debug explicitly enables it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Online OCR Engine Independently (Priority: P1)

As a developer, I need the free online OCR engine to process a sample image
through a common OCR interface so that later phases can use it as the primary
online reading option.

**Why this priority**: The full assistant depends on a free online-first OCR
path. Proving this engine independently reduces risk before cascade behavior is
added.

**Independent Test**: Given an opt-in free online OCR credential and a small
local or mockable Arabic, English, or mixed printed-text image, the engine
returns a structured OCR result with success status, raw text, duration, engine
name, and a clear failure reason when the request cannot complete.

**Acceptance Scenarios**:

1. **Given** a valid free online OCR configuration and a readable sample image,
   **When** the developer runs the online OCR engine test, **Then** a successful
   OCR result contains detected raw text and the selected engine name.
2. **Given** the online OCR service is unavailable or returns an error, **When**
   the developer runs the online OCR engine test, **Then** the program returns a
   structured failure without crashing.
3. **Given** the online OCR provider times out or has a transient failure,
   **When** the engine retries once and still cannot complete, **Then** the
   result contains timeout or provider failure metadata without logging raw OCR
   text by default.
4. **Given** no online OCR credential is configured, **When** the developer runs
   local-only tests, **Then** live online OCR tests are skipped without failing
   unrelated local engine tests.

---

### User Story 2 - Validate Local Accuracy OCR Fallback Independently (Priority: P2)

As a developer, I need the local accuracy OCR engine to process sample Arabic,
English, and mixed text images without internet access so that the assistant has
a dependable offline fallback.

**Why this priority**: Offline reading is a core project promise. The local
accuracy engine must be proven before it is used in a later fallback cascade.

**Independent Test**: With internet disabled or unused, the local accuracy engine
processes small local fixtures or mockable image inputs and returns structured
results. The engine is not loaded until it is first used.

**Acceptance Scenarios**:

1. **Given** the local accuracy OCR engine is installed and a readable sample
   image exists, **When** the developer runs the local OCR engine test, **Then**
   the result includes detected raw text, duration, success status, and engine
   name.
2. **Given** the local accuracy OCR engine is unavailable or cannot load, **When**
   the developer runs the engine test, **Then** the program returns a structured
   failure without crashing.
3. **Given** the project is imported but no OCR is requested, **When** the
   developer starts the bootstrap or imports the package, **Then** the heavy
   local OCR engine is not loaded.
4. **Given** the local accuracy engine returns empty or weak output, **When** the
   result is evaluated, **Then** the result is classified as no-text or
   weak-result failure rather than successful OCR.

---

### User Story 3 - Validate Emergency OCR Fallback Independently (Priority: P3)

As a developer, I need the emergency OCR engine to process Arabic and English
sample images so that the assistant has a final fallback when other engines fail.

**Why this priority**: Emergency OCR provides graceful degradation and keeps the
future reading workflow recoverable when the primary engines are unavailable.

**Independent Test**: The emergency OCR engine processes small local fixtures or
mockable image inputs with Arabic and English language support and returns
structured success or failure results without crashing.

**Acceptance Scenarios**:

1. **Given** the emergency OCR engine and Arabic/English language data are
   installed, **When** the developer runs the emergency OCR engine test, **Then**
   a structured result includes detected raw text, duration, success status, and
   engine name.
2. **Given** the emergency OCR executable or language data is missing, **When**
   the developer runs the engine test, **Then** the result contains a stable
   installation or language-data error code.
3. **Given** a poor or unreadable image, **When** the emergency engine is run,
   **Then** it returns a structured weak or no-text result rather than throwing
   an uncaught exception.

---

### Edge Cases

- Online OCR credential is missing.
- Online OCR provider is unavailable, times out, or returns a malformed response.
- Online OCR provider has a transient failure after the first request.
- A sample image path does not exist.
- A sample image contains no readable text.
- A sample image contains Arabic only, English only, or mixed Arabic/English.
- The local accuracy engine package or model cannot load.
- The emergency OCR executable is missing.
- Arabic or English language data for the emergency OCR engine is missing.
- OCR output is empty, very short, or contains unexpected symbols.
- OCR duration must still be captured when an engine fails.
- Raw OCR text must not appear in default logs.
- Engine tests run on a development machine without Raspberry Pi camera
  hardware.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a common OCR engine interface that every
  Phase 1 engine uses.
- **FR-002**: Every OCR engine MUST return a structured OCR result with engine
  name, raw text when available, success status, duration, optional confidence or
  quality value, fallback flag, and failure details when applicable.
- **FR-003**: The online OCR engine MUST process image files or image bytes using
  the configured free online provider when credentials are available.
- **FR-004**: The online OCR engine MUST handle missing credentials, network
  failure, provider errors, malformed responses, timeout conditions, and one
  transient retry without crashing.
- **FR-005**: The local accuracy OCR engine MUST support Arabic, English, and
  mixed printed text samples without requiring internet access.
- **FR-006**: The local accuracy OCR engine MUST lazy-load its heavy model only
  when OCR is requested.
- **FR-007**: The emergency OCR engine MUST support Arabic and English language
  data and return explicit errors when executable or language data requirements
  are missing.
- **FR-008**: Each engine MUST be testable independently before any OCR cascade
  controller is built.
- **FR-009**: Phase 1 MUST include small local sample fixtures or mockable image
  inputs sufficient to verify each engine's success and failure behavior.
- **FR-010**: Engine failures MUST use stable error codes and human-readable
  messages suitable for later spoken feedback.
- **FR-011**: Phase 1 MUST NOT implement camera capture, image-quality
  pre-checking, best-frame selection, OCR cascade routing, text cleanup, voice
  commands, TTS reading, or translation.
- **FR-012**: Online tests that require external credentials MAY be skipped when
  credentials are absent, but local unit tests MUST still pass without internet.
- **FR-013**: Empty or weak OCR output MUST be returned as `NO_TEXT_DETECTED` or
  `WEAK_OCR_RESULT` failure instead of successful OCR.
- **FR-014**: Default logs MUST include OCR metadata such as engine name,
  duration, success status, and error code, but MUST NOT include raw OCR text
  unless debug text logging is explicitly enabled.
- **FR-015**: Live online OCR tests MUST be opt-in and MUST be skipped by default
  when free credentials are absent.

### Constitution Requirements

- **CR-001**: Phase 1 MUST preserve accessibility-first behavior by producing
  failure messages that can later be mapped to spoken feedback.
- **CR-002**: Phase 1 MUST preserve accuracy-before-speed by returning enough
  metadata for later quality evaluation, without accepting silent empty results
  as successful.
- **CR-003**: Phase 1 MUST use free-only online OCR behavior and MUST NOT require
  a paid OCR service.
- **CR-004**: Phase 1 MUST preserve offline fallback readiness by validating
  local accuracy and emergency engines independently.
- **CR-005**: Phase 1 MUST preserve privacy defaults by avoiding permanent image
  storage beyond explicit test fixtures and by avoiding sensitive raw text logs
  unless debug settings allow them in later phases.
- **CR-006**: Phase 1 MUST preserve Raspberry Pi resource awareness by preventing
  heavy local OCR model loading during import or bootstrap.

### Key Entities *(include if feature involves data)*

- **OCR Engine Interface**: Shared contract that accepts an OCR request and
  returns an OCR result.
- **OCR Request**: A request to process one image, with language hints, OCR mode,
  preprocessing variant placeholder, and online/offline permission flags.
- **OCR Result**: Structured outcome containing engine name, raw text, optional
  clean text placeholder, optional confidence, quality score placeholder,
  duration, success flag, error code/message, fallback-used flag, and metadata
  safe for default logs.
- **OCR Engine Error**: Stable failure classification for missing credentials,
  network failure, provider error, model load failure, executable missing,
  language data missing, timeout, no text detected, weak OCR result, and
  unexpected engine failure.
- **Sample Image Fixture**: A local test image used to validate Arabic, English,
  mixed text, and failure scenarios without camera hardware. Fixtures must be
  small, intentional, and safe to store in the repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the three OCR engines can be invoked independently through
  the shared OCR interface.
- **SC-002**: For readable sample images, each available engine returns a
  structured result containing engine name, raw text, duration, and success
  status.
- **SC-003**: At least five failure scenarios are covered by tests or documented
  test cases: missing online credential, online provider failure, local model
  load failure, emergency OCR executable missing, and no text detected.
- **SC-004**: Importing the project or running bootstrap help does not load the
  heavy local accuracy OCR model.
- **SC-005**: Local tests can run without internet, camera hardware, audio
  devices, or paid service credentials.
- **SC-006**: No Phase 1 code path requires paid OCR services or cloud storage.
- **SC-007**: Default OCR logs contain engine metadata and failure codes but no
  raw OCR text.
- **SC-008**: Live online OCR tests can be omitted on machines without free
  credentials while the local test suite still passes.

## Assumptions

- Phase 1 builds engine prototypes only; the OCR cascade is deferred to a later
  phase.
- Camera capture and image-quality pre-checking are not required in Phase 1;
  tests use local image fixtures or controlled image inputs.
- Live online OCR tests may require an optional free credential and may be
  skipped by default when the credential is absent.
- Local engine availability may vary by development machine, so missing external
  executables or models must produce structured failures instead of crashing.
- Raw OCR text may appear in test assertions or controlled fixtures, but
  production-style verbose logging of sensitive text remains disabled by
  default.
- Online OCR calls use a configurable timeout and at most one retry for
  transient failures in Phase 1.
