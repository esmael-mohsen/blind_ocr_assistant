# Implementation Plan: Phase 3 Camera Integration and Best Frame Selection

**Branch**: `004-camera-frame-selection` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-camera-frame-selection/spec.md`

## Summary

Implement the local camera integration layer and deterministic best-frame
selection for the Blind OCR Assistant. Phase 3 will prefer the target depth
camera, fall back to generic RGB capture, capture a bounded 10-20 frame burst,
score candidates using Phase 2 image quality plus stability and optional depth
distance, and return the best acceptable frame or actionable recapture guidance.
The feature remains independent from OCR execution, OCR cascade routing, text
cleanup, voice commands, TTS, translation, and the full assistant workflow.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Phase 0-2 modules, especially
`modules/image_processing`; OpenCV-compatible camera access through
`opencv-python` or `opencv-python-headless` for generic RGB capture; `numpy` for
RGB/depth arrays and deterministic fixtures; dataclasses and enums for
structured camera models; optional Orbbec SDK or OpenNI2 behind an isolated
adapter boundary; `pytest`, `pytest-mock`, and `pytest-cov` for tests.

**Storage**: Local filesystem only. Captured frames are kept in memory by
default. Permanent frame saving is disabled unless explicit debug configuration
is introduced later. Safe fixtures may live under
`tests/fixtures/images/phase3/`. No database, cloud storage, or automatic image
retention is used.

**Testing**: Unit tests for capture request clamping, camera source fallback
order, frame candidate validation, depth classification, RGB-only degradation,
frame scoring, deterministic tie-breaks, partial timeout behavior, no-frame
timeout failure, resource release after success/failure/timeout/cancellation,
privacy-safe logs, and scope boundaries that prevent OCR or assistant workflow
behavior. Live hardware checks are opt-in/manual through a camera test script.

**Target Platform**: Raspberry Pi OS or Ubuntu-based Linux on Raspberry Pi 4
Model B with Orbbec Astra Pro as the target depth camera. Development and local
CI run on Windows/Linux without camera hardware using mocked camera sources.

**Project Type**: Single local Python assistant application with importable
camera modules and a developer-facing camera validation script.

**Performance Goals**: Capture and score one bounded burst per request, normally
15 frames and always clamped to 10-20. Do not perform continuous every-frame
analysis or OCR. Avoid unbounded frame queues, repeated large image copies, and
resource leaks. Keep camera resource lifetime scoped to a single capture
operation.

**Constraints**: No paid service, no mandatory cloud dependency, no OCR
execution, no OCR cascade, no text cleanup, no voice command recognition, no TTS
playback, no translation, and no full assistant workflow in Phase 3. Depth is an
enhancement only; RGB-only mode must remain valid. Automated tests must pass
without physical camera hardware.

**Scale/Scope**: One capture request at a time, producing one bounded set of
frame candidates plus a structured best-frame selection result. New work is
limited to `modules/camera/*`, `scripts/test_camera.py`, Phase 3 unit tests,
optional/manual hardware validation, and feature documentation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Accessibility First: PASS. Capture and recapture outcomes include short,
  actionable guidance messages suitable for later spoken feedback, with no
  required visual UI.
- Accuracy Before Speed: PASS. The feature selects from a bounded burst instead
  of forwarding an arbitrary frame, and poor or uncertain bursts return
  recapture guidance.
- Free Online-First, Offline-Fallback: PASS. Phase 3 is local-only and requires
  no paid, online, OCR, STT, TTS, translation, or cloud service.
- Graceful Degradation: PASS. The camera source order prefers the target depth
  camera and falls back to generic RGB; depth absence degrades to RGB-only
  selection; capture failures return stable codes and messages.
- Privacy by Default: PASS. Frames remain in memory by default. Default logs
  contain safe metadata only and no image contents, permanent paths, or OCR text.
- Modular Engines: PASS. Camera capture, depth analysis, and frame selection are
  isolated from OCR engines, command handling, speaking, translation, and full
  workflow orchestration.
- Testability and Observability: PASS. Deterministic fixtures, mocked camera
  sources, score breakdowns, fallback mode, distance status, selected frame id,
  and failure codes are planned.
- Raspberry Pi Resource Awareness: PASS. Frame counts, timeouts, memory use,
  and camera resource lifetimes are bounded, and resources are released on all
  terminal paths.

Post-design re-check: PASS. Research, data model, contracts, and quickstart keep
Phase 3 scoped to camera capture and best-frame selection, with no constitution
violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-camera-frame-selection/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- camera-frame-contract.md
|-- checklists/
|   `-- requirements.md
`-- spec.md
```

### Source Code (repository root)

```text
modules/
|-- camera/
|   |-- __init__.py
|   |-- camera_models.py
|   |-- orbbec_camera.py
|   |-- depth_analyzer.py
|   `-- frame_selector.py
|-- image_processing/
|   |-- image_models.py
|   `-- quality_checker.py
`-- common/
    |-- logging.py
    `-- result.py

scripts/
`-- test_camera.py

tests/
|-- unit/
|   |-- test_camera_models.py
|   |-- test_camera_capture.py
|   |-- test_depth_analyzer.py
|   |-- test_frame_selector.py
|   `-- test_camera_logging_privacy.py
|-- integration/
|   `-- test_camera_live_optional.py
`-- fixtures/
    `-- images/
        `-- phase3/
            `-- README.md
```

**Structure Decision**: Extend the existing modular scaffold with a new
`modules/camera/*` layer that consumes Phase 2 image-quality reports but does
not call OCR or assistant orchestration. Automated tests use mocks and fixtures;
live hardware validation stays opt-in through `scripts/test_camera.py`.

## Complexity Tracking

No constitution violations or complexity exceptions are required for Phase 3.
