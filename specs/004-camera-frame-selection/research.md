# Research: Phase 3 Camera Integration and Best Frame Selection

## Decision: Automated tests use mocked camera sources; live hardware is opt-in

**Rationale**: Local development and CI must pass without an Orbbec Astra Pro or
any physical camera. Mocked sources make capture success, failure, timeout,
partial timeout, invalid frames, and depth availability deterministic.

**Alternatives considered**: Requiring hardware for all validation was rejected
because it would block development machines. Skipping camera behavior entirely
was rejected because resource release and selection logic need automated
coverage.

## Decision: Prefer target depth camera, then generic RGB fallback

**Rationale**: The target hardware can provide useful depth guidance, but Phase
3 must still work on development machines and on RGB-only camera paths. Source
selection will attempt the target depth adapter first and use the generic RGB
adapter when the target path is unavailable or unsupported.

**Alternatives considered**: Generic RGB first was rejected because it would
hide target-camera regressions. Failing when depth is absent was rejected
because RGB-only mode is an accepted degraded path.

## Decision: Clamp burst count to 10-20 frames, defaulting to 15

**Rationale**: The project implementation plan requires best-frame selection
from 10-20 frames. Clamping makes out-of-range configuration safe and predictable
without surprising failures for minor configuration mistakes.

**Alternatives considered**: Rejecting out-of-range requests was rejected
because the accepted clarification selected clamping. Allowing arbitrary counts
was rejected because it risks memory and latency issues on Raspberry Pi.

## Decision: Score partial timeout frames when at least one valid frame exists

**Rationale**: A partial burst can still contain a usable frame. The result will
record that a timeout occurred, score valid frames, and fail only when zero valid
frames were captured.

**Alternatives considered**: Failing every partial timeout was rejected because
it discards useful captures. Ignoring the timeout was rejected because callers
need observability for degraded capture behavior.

## Decision: Frame score combines Phase 2 quality, stability, and optional depth

**Rationale**: Phase 2 already produces the main image-quality signal needed for
OCR readiness. Phase 3 adds burst-specific stability and optional distance
signals. Image quality remains dominant; distance and stability refine the
choice without making depth mandatory.

**Alternatives considered**: Using sharpness only was rejected because readable
OCR also depends on lighting, contrast, and text presence. Making depth dominate
was rejected because noisy or unavailable depth must not defeat strong RGB
quality.

## Decision: Tie-break by acceptable quality, then stability, then earliest frame

**Rationale**: Deterministic tie-breaking is required for repeatable tests and
predictable behavior. The accepted clarification prioritizes acceptable image
quality, then stability, then earliest capture order.

**Alternatives considered**: Random selection was rejected because it is
untestable and confusing. Latest-frame preference was rejected because earlier
frames are equally valid once scores and stability match.

## Decision: Depth categories use fixed default thresholds

**Rationale**: The accepted defaults classify document distance as too close
below 25 cm, acceptable from 25 cm through 75 cm, too far above 75 cm, or
unavailable. These thresholds provide simple guidance without calibration.

**Alternatives considered**: Camera-specific calibration was deferred because it
adds hardware complexity. Ignoring depth was rejected because the target camera
can improve capture guidance.

## Decision: Camera resources are released through scoped cleanup

**Rationale**: Camera handles must not leak in a long-running assistant process.
Capture operations should use context-manager style ownership or `try/finally`
cleanup so resources release exactly once after success, failure, timeout, or
cancellation.

**Alternatives considered**: Relying on object destructors was rejected because
cleanup timing is not explicit. Leaving resources open across requests was
rejected because it complicates recovery from hardware failures.

## Decision: Default logging is metadata-only

**Rationale**: Captured images may contain sensitive personal text. Logs should
record frame count, source type, fallback mode, selected frame id, score summary,
distance status, timeout flag, cleanup status, and failure code, but not image
contents, raw arrays, OCR text, or permanent debug paths.

**Alternatives considered**: Saving every captured frame was rejected for
privacy and storage reasons. Logging detailed image payloads was rejected because
it exposes user content and is not needed for default observability.
