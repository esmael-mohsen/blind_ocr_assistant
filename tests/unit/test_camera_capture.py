"""Phase 3 camera capture and cleanup tests."""

from __future__ import annotations

import numpy as np
import pytest

from modules.camera.camera_models import (
    CameraErrorCode,
    CameraSourceType,
    CaptureRequest,
    CleanupStatus,
)
from modules.camera.orbbec_camera import capture_burst_from_sources


def _image(level: int = 127) -> np.ndarray:
    return np.full((8, 8, 3), level, dtype=np.uint8)


class FakeSource:
    def __init__(
        self,
        source_type: CameraSourceType,
        frames: list[object] | None = None,
        *,
        open_success: bool = True,
        source_id: str = "fake",
    ) -> None:
        self.source_type = source_type
        self.source_id = source_id
        self.supports_rgb = True
        self.supports_depth = source_type == CameraSourceType.TARGET_DEPTH
        self.frames = list(frames or [])
        self.open_success = open_success
        self.open_count = 0
        self.release_count = 0

    def open(self) -> bool:
        self.open_count += 1
        return self.open_success

    def capture_frame(self) -> object:
        if not self.frames:
            raise TimeoutError("no frames")
        frame = self.frames.pop(0)
        if isinstance(frame, BaseException):
            raise frame
        return frame

    def release(self) -> None:
        self.release_count += 1


def test_prefers_target_depth_source_before_generic_rgb_fallback() -> None:
    target = FakeSource(CameraSourceType.TARGET_DEPTH, frames=[_image() for _ in range(10)])
    generic = FakeSource(CameraSourceType.GENERIC_RGB, frames=[_image() for _ in range(10)])

    result = capture_burst_from_sources(
        [target, generic],
        CaptureRequest(requested_count=10),
    )

    assert result.success is True
    assert result.source_type == CameraSourceType.TARGET_DEPTH
    assert target.open_count == 1
    assert generic.open_count == 0
    assert target.release_count == 1


def test_falls_back_to_generic_rgb_when_target_depth_open_fails() -> None:
    target = FakeSource(CameraSourceType.TARGET_DEPTH, open_success=False)
    generic = FakeSource(CameraSourceType.GENERIC_RGB, frames=[_image() for _ in range(10)])

    result = capture_burst_from_sources(
        [target, generic],
        CaptureRequest(requested_count=10),
    )

    assert result.success is True
    assert result.source_type == CameraSourceType.GENERIC_RGB
    assert target.release_count == 1
    assert generic.release_count == 1


def test_successful_rgb_burst_returns_candidates_metadata_and_cleanup() -> None:
    source = FakeSource(
        CameraSourceType.GENERIC_RGB,
        frames=[_image(i + 20) for i in range(10)],
        source_id="rgb-0",
    )

    result = capture_burst_from_sources([source], CaptureRequest(requested_count=2))

    assert result.success is True
    assert len(result.candidates) == 10
    assert result.cleanup_status == CleanupStatus.RELEASED
    assert result.candidates[0].frame_id == "rgb-0-0"
    assert result.candidates[0].metadata["source_type"] == CameraSourceType.GENERIC_RGB.value
    assert result.candidates[0].metadata["image_width"] == 8
    assert source.release_count == 1


def test_releases_resources_once_after_terminal_paths() -> None:
    success = FakeSource(CameraSourceType.GENERIC_RGB, frames=[_image() for _ in range(10)])
    capture_burst_from_sources([success], CaptureRequest(requested_count=10))
    assert success.release_count == 1

    open_failure = FakeSource(CameraSourceType.GENERIC_RGB, open_success=False)
    capture_burst_from_sources([open_failure], CaptureRequest(requested_count=10))
    assert open_failure.release_count == 1

    timeout = FakeSource(CameraSourceType.GENERIC_RGB, frames=[TimeoutError("timeout")])
    capture_burst_from_sources([timeout], CaptureRequest(requested_count=10))
    assert timeout.release_count == 1

    cancelled = FakeSource(CameraSourceType.GENERIC_RGB, frames=[KeyboardInterrupt()])
    with pytest.raises(KeyboardInterrupt):
        capture_burst_from_sources([cancelled], CaptureRequest(requested_count=10))
    assert cancelled.release_count == 1


def test_invalid_frames_return_stable_frame_errors() -> None:
    empty = FakeSource(CameraSourceType.GENERIC_RGB, frames=[np.array([], dtype=np.uint8)])
    empty_result = capture_burst_from_sources([empty], CaptureRequest(requested_count=10))
    assert empty_result.success is False
    assert empty_result.error.error_code == CameraErrorCode.CAMERA_EMPTY_FRAME

    invalid = FakeSource(
        CameraSourceType.GENERIC_RGB,
        frames=[np.zeros((2, 2, 2), dtype=np.uint8)],
    )
    invalid_result = capture_burst_from_sources([invalid], CaptureRequest(requested_count=10))
    assert invalid_result.success is False
    assert invalid_result.error.error_code == CameraErrorCode.CAMERA_INVALID_FRAME


def test_partial_timeout_scores_valid_frames_and_zero_timeout_fails() -> None:
    partial = FakeSource(CameraSourceType.GENERIC_RGB, frames=[_image(), TimeoutError("timeout")])
    partial_result = capture_burst_from_sources([partial], CaptureRequest(requested_count=10))

    assert partial_result.success is True
    assert partial_result.partial_timeout is True
    assert len(partial_result.candidates) == 1
    assert partial_result.selection_result is not None

    zero = FakeSource(CameraSourceType.GENERIC_RGB, frames=[TimeoutError("timeout")])
    zero_result = capture_burst_from_sources([zero], CaptureRequest(requested_count=10))

    assert zero_result.success is False
    assert zero_result.error.error_code == CameraErrorCode.CAMERA_CAPTURE_TIMEOUT
