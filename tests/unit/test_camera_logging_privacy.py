"""Phase 3 camera privacy and safe logging tests."""

from __future__ import annotations

import numpy as np

from modules.camera.camera_models import (
    BestFrameSelectionResult,
    CameraSourceType,
    CleanupStatus,
    DepthReport,
    DistanceStatus,
    FrameCandidate,
    camera_log_metadata,
    sanitize_camera_metadata,
)


def test_camera_metadata_sanitizer_excludes_sensitive_payloads() -> None:
    metadata = sanitize_camera_metadata(
        {
            "image": np.zeros((2, 2, 3), dtype=np.uint8),
            "rgb_image": np.zeros((2, 2, 3), dtype=np.uint8),
            "depth_map": np.ones((2, 2), dtype=np.float32),
            "raw_text": "private OCR text",
            "clean_text": "private clean text",
            "debug_path": "debug_captures/private.png",
            "token": "secret",
            "source_type": "mock",
            "frame_count": 2,
        }
    )

    assert metadata == {"source_type": "mock", "frame_count": 2}


def test_camera_log_metadata_excludes_frame_and_depth_payloads() -> None:
    candidate = FrameCandidate(
        frame_id="safe",
        rgb_image=np.zeros((4, 4, 3), dtype=np.uint8),
        depth_map=np.ones((4, 4), dtype=np.float32),
        timestamp=1.0,
        capture_order=0,
        source_id="mock",
        depth_report=DepthReport(
            status=DistanceStatus.ACCEPTABLE,
            distance_cm=40.0,
            score_contribution=0.1,
            guidance="Distance is acceptable.",
        ),
    )
    result = BestFrameSelectionResult(
        success=True,
        selected_frame=candidate,
        candidate_summaries=[candidate.safe_summary()],
        guidance="Ready.",
        source_type=CameraSourceType.MOCK,
        cleanup_status=CleanupStatus.RELEASED,
    )

    metadata = camera_log_metadata(result)
    as_text = repr(metadata)

    assert metadata["selected_frame_id"] == "safe"
    assert "rgb_image" not in as_text
    assert "depth_map" not in as_text
    assert "private" not in as_text
    assert "debug_captures" not in as_text
