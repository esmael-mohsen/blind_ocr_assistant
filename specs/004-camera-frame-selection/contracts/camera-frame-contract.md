# Contract: Camera Capture and Best Frame Selection

## Scope

This contract defines the Phase 3 internal Python interfaces for camera capture,
depth guidance, and best-frame selection. It is not an HTTP API and does not
perform OCR, text cleanup, voice command handling, TTS, translation, or full
assistant orchestration.

## Camera Source Contract

Camera sources expose a common interface:

```text
open() -> CameraOpenResult
capture_frame() -> FrameCaptureResult
capture_burst(request: CaptureRequest) -> CaptureBurstResult
release() -> ResourceReleaseResult
```

**Required behavior**

- `open()` initializes one camera source and returns a stable success or failure.
- `capture_frame()` returns one RGB frame and optional depth data when available.
- `capture_burst()` attempts up to the clamped request count within the timeout.
- `release()` releases resources exactly once and is safe to call after partial
  failures.
- Target depth camera adapters must be tried before generic RGB adapters.
- Generic RGB capture must remain valid when depth is unavailable.

## Capture Request Contract

```text
CaptureRequest
- requested_count: int | None
- capture_count: int
- timeout_seconds: float
- prefer_depth: bool
- allow_rgb_fallback: bool
- debug_save_enabled: bool
```

**Required behavior**

- Requests below 10 frames are clamped to 10.
- Requests above 20 frames are clamped to 20.
- Missing request count defaults to 15.
- Debug frame saving defaults to false.
- Invalid timeouts return a structured failure instead of uncaught exceptions.

## Capture Result Contract

```text
CaptureBurstResult
- success: bool
- candidates: list[FrameCandidate]
- source_type: target_depth | generic_rgb | mock
- partial_timeout: bool
- error_code: str | None
- message: str
- cleanup_status: released | release_failed
```

**Required behavior**

- If at least one valid frame is captured before timeout, return those frames
  with `partial_timeout=true`.
- If zero valid frames are captured before timeout, return
  `CAMERA_CAPTURE_TIMEOUT`.
- Empty, corrupted, or dimensionally invalid frames are excluded or returned as
  structured invalid-frame failures.
- Results must include only safe metadata, not image payloads in logs.

## Depth Analysis Contract

```text
analyze_depth(depth_map, rgb_shape=None) -> DepthReport
```

**Required behavior**

- Below 25 cm returns `too_close`.
- 25 cm through 75 cm returns `acceptable`.
- Above 75 cm returns `too_far`.
- Missing, unsupported, noisy, unaligned, or invalid depth returns
  `unavailable`.
- Depth unavailability is not fatal when RGB capture succeeds.
- Guidance messages must be short and suitable for later spoken feedback.

## Frame Selection Contract

```text
select_best_frame(candidates: list[FrameCandidate]) -> BestFrameSelectionResult
```

**Required behavior**

- Every candidate is scored with Phase 2 quality signals plus stability and
  optional depth distance.
- The highest-scoring acceptable frame is selected.
- If no candidate is acceptable, return `NO_ACCEPTABLE_FRAME` and recapture
  guidance.
- Similar scores are resolved by acceptable image quality first, stability
  second, and earliest capture order third.
- Selection is deterministic for the same ordered input frames and thresholds.

## Error Contract

Expected error codes:

```text
CAMERA_OPEN_FAILED
CAMERA_CAPTURE_TIMEOUT
CAMERA_EMPTY_FRAME
CAMERA_INVALID_FRAME
CAMERA_DEPTH_UNAVAILABLE
NO_ACCEPTABLE_FRAME
CAMERA_RESOURCE_RELEASE_FAILED
CAMERA_UNEXPECTED_ERROR
```

Each error must include a developer-safe message and, where appropriate, a short
user guidance message. Errors must not expose image contents, raw arrays,
sensitive text, secrets, or permanent debug paths.

## Logging and Privacy Contract

Default logs may include:

- source type and fallback mode
- requested and clamped frame count
- number of valid candidates
- selected frame id
- quality score summary
- distance status
- partial timeout flag
- cleanup status
- failure code

Default logs must not include:

- RGB image contents
- depth map contents
- OCR text
- permanent debug image paths
- secrets or credentials

## Phase Boundary Contract

Phase 3 must not call OCR engines, OCR cascade controllers, text cleanup,
translation, TTS, voice command recognition, or full assistant workflow
controllers. It returns the selected frame and guidance for later phases to
consume.
