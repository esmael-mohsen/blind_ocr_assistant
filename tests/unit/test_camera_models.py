"""Phase 3 camera model validation tests."""

from __future__ import annotations

import numpy as np
import pytest

from modules.camera.camera_models import (
    BestFrameSelectionResult,
    CameraError,
    CameraErrorCode,
    CameraSourceType,
    CaptureRequest,
    CleanupStatus,
    DepthReport,
    DistanceStatus,
    FrameCandidate,
    FrameScore,
    camera_log_metadata,
    sanitize_camera_metadata,
)


def _image(width: int = 8, height: int = 6) -> np.ndarray:
    return np.full((height, width, 3), 127, dtype=np.uint8)


def test_capture_request_clamps_count_and_keeps_debug_disabled() -> None:
    assert CaptureRequest(requested_count=None).capture_count == 15
    assert CaptureRequest(requested_count=1).capture_count == 10
    assert CaptureRequest(requested_count=999).capture_count == 20
    assert CaptureRequest(requested_count=12).capture_count == 12
    assert CaptureRequest(requested_count=12).debug_save_enabled is False


def test_capture_request_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="timeout"):
        CaptureRequest(timeout_seconds=0)

    with pytest.raises(ValueError, match="timeout"):
        CaptureRequest(timeout_seconds=-1)


def test_camera_error_and_frame_candidate_safe_metadata() -> None:
    candidate = FrameCandidate(
        frame_id="frame-1",
        rgb_image=_image(),
        timestamp=1.0,
        capture_order=0,
        source_id="mock",
        metadata={
            "debug_path": "debug_captures/secret.png",
            "ocr_text": "private text",
            "safe_value": "kept",
        },
    )
    assert candidate.metadata["safe_value"] == "kept"
    assert candidate.metadata["image_width"] == 8
    assert candidate.metadata["image_height"] == 6
    assert "debug_path" not in candidate.metadata
    assert "ocr_text" not in candidate.metadata

    error = CameraError(
        error_code=CameraErrorCode.CAMERA_OPEN_FAILED,
        message="camera unavailable",
        guidance="Try again.",
    )
    assert error.error_code == CameraErrorCode.CAMERA_OPEN_FAILED
    assert "camera unavailable" in error.message


def test_frame_score_depth_report_and_selection_result_safe_summary() -> None:
    depth = DepthReport(
        status=DistanceStatus.ACCEPTABLE,
        distance_cm=40.0,
        score_contribution=0.1,
        guidance="Distance is acceptable.",
    )
    score = FrameScore(
        quality_score=0.9,
        quality_acceptable=True,
        stability_score=0.8,
        distance_score=depth.score_contribution,
        total_score=0.86,
        tie_quality_rank=1,
        tie_stability_rank=0.8,
        tie_order_rank=0,
    )
    candidate = FrameCandidate(
        frame_id="frame-1",
        rgb_image=_image(),
        depth_map=np.ones((6, 8), dtype=np.float32),
        timestamp=1.0,
        capture_order=0,
        source_id="mock",
        depth_report=depth,
        frame_score=score,
        metadata={"raw_image": _image(), "source_type": CameraSourceType.MOCK.value},
    )
    result = BestFrameSelectionResult(
        success=True,
        selected_frame=candidate,
        candidate_summaries=[candidate.safe_summary()],
        guidance="Ready.",
        source_type=CameraSourceType.MOCK,
        cleanup_status=CleanupStatus.RELEASED,
    )

    summary = result.candidate_summaries[0]
    assert summary["frame_id"] == "frame-1"
    assert summary["distance_status"] == DistanceStatus.ACCEPTABLE.value
    assert "rgb_image" not in summary
    assert "depth_map" not in summary
    assert result.selected_frame is candidate


def test_sanitize_camera_metadata_blocks_sensitive_values() -> None:
    safe = sanitize_camera_metadata(
        {
            "image": _image(),
            "depth_map": np.ones((2, 2)),
            "raw_text": "secret",
            "secret": "hidden",
            "token": "hidden",
            "source_type": "mock",
            "frame_count": 3,
        }
    )

    assert safe == {"source_type": "mock", "frame_count": 3}


def test_camera_log_metadata_contains_safe_result_fields_only() -> None:
    error = CameraError(
        error_code=CameraErrorCode.CAMERA_CAPTURE_TIMEOUT,
        message="timeout",
    )
    result = BestFrameSelectionResult(
        success=False,
        selected_frame=None,
        candidate_summaries=[],
        guidance="Try again.",
        source_type=CameraSourceType.GENERIC_RGB,
        partial_timeout=True,
        error=error,
        cleanup_status=CleanupStatus.RELEASED,
    )

    metadata = camera_log_metadata(result)

    assert metadata["success"] is False
    assert metadata["source_type"] == CameraSourceType.GENERIC_RGB.value
    assert metadata["partial_timeout"] is True
    assert metadata["error_code"] == CameraErrorCode.CAMERA_CAPTURE_TIMEOUT.value
    assert "selected_frame" not in metadata
