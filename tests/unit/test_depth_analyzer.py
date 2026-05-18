"""Phase 3 depth analyzer tests."""

from __future__ import annotations

import numpy as np

from modules.camera.camera_models import DistanceStatus
from modules.camera.depth_analyzer import analyze_depth


def test_depth_below_25_cm_is_too_close() -> None:
    report = analyze_depth(np.full((4, 4), 20.0, dtype=np.float32))

    assert report.status == DistanceStatus.TOO_CLOSE
    assert report.distance_cm == 20.0
    assert report.score_contribution < 0
    assert "farther" in report.guidance.lower()


def test_depth_25_through_75_cm_is_acceptable() -> None:
    assert analyze_depth(np.full((4, 4), 25.0, dtype=np.float32)).status == (
        DistanceStatus.ACCEPTABLE
    )
    assert analyze_depth(np.full((4, 4), 75.0, dtype=np.float32)).status == (
        DistanceStatus.ACCEPTABLE
    )


def test_depth_above_75_cm_is_too_far() -> None:
    report = analyze_depth(np.full((4, 4), 80.0, dtype=np.float32))

    assert report.status == DistanceStatus.TOO_FAR
    assert report.distance_cm == 80.0
    assert report.score_contribution < 0
    assert "closer" in report.guidance.lower()


def test_missing_noisy_unsupported_or_invalid_depth_is_unavailable() -> None:
    for depth in (
        None,
        np.array([], dtype=np.float32),
        np.full((4, 4), np.nan, dtype=np.float32),
        np.full((4, 4), -1.0, dtype=np.float32),
        "not-depth",
    ):
        report = analyze_depth(depth)
        assert report.status == DistanceStatus.UNAVAILABLE
        assert report.distance_cm is None
        assert report.score_contribution == 0.0
