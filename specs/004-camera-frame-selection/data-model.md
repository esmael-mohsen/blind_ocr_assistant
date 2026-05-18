# Data Model: Phase 3 Camera Integration and Best Frame Selection

## CameraSource

Represents a real, fallback, or mocked camera provider.

**Fields**

- `source_id`: Stable source identifier for logs and results.
- `source_type`: `target_depth`, `generic_rgb`, or `mock`.
- `supports_rgb`: Whether RGB capture is available.
- `supports_depth`: Whether depth capture is available.
- `metadata`: Safe hardware or adapter metadata, excluding image contents.
- `is_open`: Current resource state.

**Rules**

- Later phases interact through the abstraction, not hardware-specific APIs.
- The target depth source is attempted before generic RGB fallback.
- `release()` must be idempotent and safe after partial open failures.

## CaptureRequest

Describes a single frame or bounded burst request.

**Fields**

- `requested_count`: Caller-requested burst size.
- `capture_count`: Clamped count used for capture.
- `timeout_seconds`: Maximum duration for the burst.
- `prefer_depth`: Whether target depth capture should be attempted first.
- `allow_rgb_fallback`: Whether generic RGB fallback may be used.
- `debug_save_enabled`: Explicit debug flag; default is false.

**Validation**

- `capture_count` is clamped to the inclusive 10-20 frame range.
- Default `capture_count` is 15 when no caller value is supplied.
- `timeout_seconds` must be positive and bounded by configuration.
- Debug saving remains disabled unless explicitly enabled.

## FrameCandidate

Represents one captured or synthetic frame that can be scored.

**Fields**

- `frame_id`: Stable identifier unique within the capture result.
- `rgb_image`: RGB image data in memory.
- `depth_map`: Optional depth data in memory.
- `timestamp`: Capture timestamp.
- `capture_order`: Zero-based or one-based order used for deterministic ties.
- `source_id`: Camera source that produced the frame.
- `quality_report`: Phase 2 image quality report.
- `depth_report`: Optional depth report.
- `stability_score`: Burst stability score.
- `distance_score`: Depth-derived score contribution.
- `total_score`: Deterministic combined score.
- `metadata`: Safe metadata such as dimensions and source type.

**Validation**

- RGB image data must be present, non-empty, and dimensionally valid.
- Depth data may be absent or invalid without failing RGB-only selection.
- Metadata must not contain image payloads, raw OCR text, or permanent debug
  paths.

## DepthReport

Describes document distance guidance for a frame.

**Fields**

- `status`: `too_close`, `acceptable`, `too_far`, or `unavailable`.
- `distance_cm`: Optional numeric distance estimate.
- `score_contribution`: Numeric contribution to the frame score.
- `guidance`: Short corrective message suitable for later spoken feedback.
- `reason`: Stable reason for unavailable or invalid depth.

**Validation**

- Below 25 cm is `too_close`.
- 25 cm through 75 cm is `acceptable`.
- Above 75 cm is `too_far`.
- Missing, noisy, unsupported, or invalid depth is `unavailable`.

## FrameScore

Contains the deterministic scoring breakdown for a candidate.

**Fields**

- `quality_score`: Phase 2 image-quality score.
- `quality_acceptable`: Whether Phase 2 considers the image acceptable.
- `stability_score`: Burst-specific stability contribution.
- `distance_score`: Depth contribution, or neutral value for RGB-only mode.
- `total_score`: Combined selection score.
- `tie_quality_rank`: Rank used for acceptable-quality tie-breaks.
- `tie_stability_rank`: Rank used for stability tie-breaks.
- `tie_order_rank`: Capture order used as the final tie-break.

**Rules**

- Quality remains the primary selection signal.
- Similar total scores are resolved by acceptable quality, then stability, then
  earliest capture order.
- The same ordered input frames and thresholds must produce the same result.

## BestFrameSelectionResult

Structured outcome returned by Phase 3.

**Fields**

- `success`: Whether an acceptable frame was selected.
- `selected_frame`: Selected `FrameCandidate` when successful.
- `candidate_summaries`: Safe score and status summaries for all candidates.
- `guidance`: Capture or recapture guidance suitable for later spoken feedback.
- `source_type`: Selected camera source path or fallback mode.
- `partial_timeout`: Whether capture timed out after at least one valid frame.
- `error`: Optional `CameraError`.
- `cleanup_status`: Whether camera resources were released.

**Rules**

- Success requires at least one acceptable selected frame.
- If all frames are poor or uncertain, no frame is selected and recapture
  guidance is returned.
- If capture times out after valid frames, valid frames are still scored and
  `partial_timeout` is true.
- If capture times out with zero valid frames, return a structured capture
  failure.

## CameraError

Stable failure classification for camera and selection paths.

**Codes**

- `CAMERA_OPEN_FAILED`
- `CAMERA_CAPTURE_TIMEOUT`
- `CAMERA_EMPTY_FRAME`
- `CAMERA_INVALID_FRAME`
- `CAMERA_DEPTH_UNAVAILABLE`
- `NO_ACCEPTABLE_FRAME`
- `CAMERA_RESOURCE_RELEASE_FAILED`
- `CAMERA_UNEXPECTED_ERROR`

**Rules**

- Expected failures return stable codes and human-readable messages.
- Expected failures must not expose image contents or hardware internals.
- Depth unavailability is non-fatal when RGB capture succeeds.

## State Transitions

```text
idle
  -> opening_camera
  -> capturing_burst
  -> scoring_candidates
  -> selected_frame | recapture_needed | capture_failed
  -> releasing_resources
  -> completed
```

All terminal paths pass through `releasing_resources`, including success,
failure, timeout, and cancellation.
