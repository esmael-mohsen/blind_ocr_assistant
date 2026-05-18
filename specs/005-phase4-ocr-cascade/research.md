# Research: Phase 4 OCR Cascade Controller

## Decision: Use a deterministic OCR quality acceptance threshold of 0.70

**Rationale**: The accepted clarification sets 0.70 as the minimum score for
accepting OCR output. This gives tests a concrete pass/fail boundary and aligns
with accuracy-before-speed: weak text should trigger fallback or final failure
rather than being read to a blind user.

**Alternatives considered**: Accepting all non-empty OCR text was rejected
because wrong text is harmful. Using only provider confidence was rejected
because not all engines expose comparable confidence.

## Decision: Score text quality with transparent heuristics

**Rationale**: Phase 4 needs deterministic local quality signals for empty text,
very short text, symbol noise, excessive spacing, repeated characters, Arabic
fragmentation, and mixed-language validity. Transparent heuristics are easy to
test and tune later with benchmarks.

**Alternatives considered**: A machine-learned quality classifier was rejected
because it adds model storage and tuning complexity. Deferring all quality
judgment to later text cleanup was rejected because cascade routing needs a
decision immediately.

## Decision: Normal online mode stops after the first acceptable result

**Rationale**: Normal mode should conserve Raspberry Pi resources and avoid
unnecessary OCR engine work. If the online primary result is acceptable, fallback
engines are not attempted.

**Alternatives considered**: Running all engines by default was rejected by the
constitution and resource constraints. Always running local OCR after online OCR
was rejected because it wastes time when online output is already good.

## Decision: Offline routing skips online OCR and starts local accuracy OCR

**Rationale**: When internet is unavailable, online OCR is disabled, or online
use is disallowed, the cascade should not wait on the online path. Local
accuracy OCR is attempted first, then emergency OCR if needed.

**Alternatives considered**: Trying online OCR despite known unavailability was
rejected because it adds latency and confusing failure. Failing immediately when
offline was rejected because offline degraded mode is required.

## Decision: High Accuracy Mode compares online and local accuracy candidates

**Rationale**: High Accuracy Mode is explicitly allowed to spend more time for
difficult documents. Comparing online primary and local accuracy results before
acceptance can improve reliability while keeping emergency OCR reserved for
cases where both stronger candidates fail or are weak.

**Alternatives considered**: Using normal cascade order in High Accuracy Mode was
rejected because it would not deliver the promised comparison. Running emergency
OCR every time was rejected because it adds resource cost with limited value.

## Decision: High Accuracy similar-score tie-break prefers local accuracy OCR

**Rationale**: The accepted clarification states that when acceptable scores
differ by less than 0.05, High Accuracy Mode prefers the local accuracy result,
then uses shorter duration as final tie-break. This avoids unnecessary upload
preference when quality is effectively tied.

**Alternatives considered**: Preferring online OCR in ties was rejected for
privacy and offline-alignment reasons. Random tie-breaking was rejected because
tests and user outcomes must be deterministic.

## Decision: Each allowed engine is attempted at most once per cascade request

**Rationale**: A one-attempt default bounds latency and resource use. Online
availability check failure or engine timeout routes to the next allowed fallback.

**Alternatives considered**: Multiple retries were rejected for the default
because they can delay spoken feedback. Unlimited retry was rejected outright.

## Decision: Image-not-ready inputs block OCR before engine attempts

**Rationale**: If previous image quality checks already rejected the selected
image, OCR should not run. The cascade returns `IMAGE_NOT_READY_FOR_OCR` with
recapture guidance.

**Alternatives considered**: Trying OCR anyway was rejected because it violates
"Do not OCR bad images" and wastes time. Silently returning no text was rejected
because the user needs actionable guidance.

## Decision: Default logs are OCR-metadata only

**Rationale**: OCR text may contain sensitive private content. Logs should record
engine path, selected engine, duration, quality score, fallback use, and failure
codes, but not OCR text unless both debug mode and sensitive-text logging are
enabled.

**Alternatives considered**: Logging raw OCR text by default was rejected for
privacy. Suppressing all cascade metadata was rejected because troubleshooting
fallback behavior needs safe observability.
