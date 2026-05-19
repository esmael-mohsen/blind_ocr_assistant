# Phase 9 Contract: Full Assistive Workflow Integration

## Scope

This contract defines internal Python-facing behavior for Phase 9 full workflow
integration. It covers assistant session state, read workflow orchestration,
translation workflow handoff, spoken status, privacy-safe metadata, busy
read-command behavior, recoverable timeout/failure handling, and graceful
operational shutdown.

It does not define new OCR engines, translation engines, speech engines,
cleanup rules, command categories, benchmark tooling, deployment services,
visual UI, user accounts, or cloud storage.

## Assistant Workflow Contract

The workflow coordinator must expose behavior equivalent to:

```python
class AssistantWorkflow:
    def handle_command(self, phrase: str, language_hint: str = "unknown") -> object: ...
    def run_read_workflow(self, *, high_accuracy: bool = False) -> object: ...
    def run_translation_workflow(self, target_language: str) -> object: ...
    def shutdown(self) -> object: ...
    def get_state(self) -> object: ...
```

### Operation Guarantees

- A recognized read command starts capture only when no read workflow is active.
- A read command during an active read workflow returns busy guidance and starts
  no second capture or OCR attempt.
- Capture uses a bounded burst through the existing camera boundary.
- Best-frame selection must accept a frame before OCR runs.
- If no acceptable frame is selected, the read attempt ends with recapture
  guidance and no automatic capture loop.
- OCR uses the existing cascade and honors online/offline configuration.
- OCR output is cleaned before any reading or translation state update.
- Cleaned text is handed to the existing reading controller.
- Translation commands use latest successful clean text and the requested target
  language.
- Voice stop remains reading playback control and does not trigger operational
  shutdown.
- Operational shutdown is supported through process interruption, service stop,
  or test harness control.

## Required Boundary Inputs

The coordinator may depend on injected boundaries equivalent to:

```python
capture_burst(request) -> CaptureBurstResult
select_best_frame(candidates) -> BestFrameSelectionResult
run_ocr_cascade(request, engines, online_status_provider=None) -> OCRCascadeResult
clean_ocr_text(request) -> TextCleanupResult
reading_controller.start_reading(clean_text, language="mixed") -> SpeechResult
translation_controller.translate_latest(clean_text, target_language, ...) -> TranslationResult
dialogue_manager.handle_command(phrase, language_hint="unknown", ...) -> CommandResult
```

### Boundary Rules

- Boundaries return structured results or are wrapped into structured workflow
  failures.
- `KeyboardInterrupt` or operational shutdown signals must release resources
  and stop active speech when possible.
- Component timeouts are recoverable workflow failures.
- Engine-specific configuration remains outside the coordinator.

## Read Workflow Result Contract

A successful read workflow result must include:

- success status
- selected OCR engine
- fallback/offline/high-accuracy status
- language classification
- cleanup status
- reading handoff status
- user-facing guidance
- safe metadata

A failed read workflow result must include:

- failure status
- stable error category
- recoverable flag
- user-facing recovery guidance
- safe metadata

## Translation Workflow Result Contract

A translation workflow result must:

- reject missing latest clean text with spoken guidance
- use latest successful clean text only
- preserve previous successful clean text and translated text on failure
- record target language and fallback status
- hand successful translated text to reading through the existing translation
  controller behavior
- exclude text payloads from safe metadata

## State Contract

Assistant state must:

- keep only latest successful text and translation state in memory
- replace latest clean text only after a successful read workflow
- replace latest translated text only after successful translation
- preserve previous successful state after recoverable failures
- clear in-memory state when the process exits
- record workflow status and last guidance

## Privacy Contract

Default logs and safe metadata may include:

- workflow operation
- workflow status
- selected engine names
- fallback/offline/high-accuracy flags
- duration
- error category
- cleanup status
- language classification
- shutdown status

Default logs and safe metadata must not include:

- images or image bytes
- depth maps
- raw OCR text
- clean text
- translated text
- command transcripts
- speech input
- text snippets
- provider secrets or endpoint credentials

## Scope Boundary Contract

Phase 9 tests must assert that this phase does not introduce or modify:

- new OCR engines
- new translation engines
- new STT or TTS engines
- new text cleanup rules
- new command categories
- benchmark data or benchmark scripts
- deployment service files
- visual UI requirements
- user account behavior
- cloud storage behavior
