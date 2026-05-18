"""Phase 3 best-frame selector tests."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from modules.camera.camera_models import (
    CameraErrorCode,
    CameraSourceType,
    DepthReport,
    DistanceStatus,
    FrameCandidate,
)
from modules.camera.frame_selector import select_best_frame


def _image(level: int = 127) -> np.ndarray:
    return np.full((8, 8, 3), level, dtype=np.uint8)


def _quality(score: float, acceptable: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        quality_score=score,
        is_acceptable=acceptable,
        guidance=SimpleNamespace(english_text="Recapture more clearly."),
    )


def _candidate(
    frame_id: str,
    *,
    order: int,
    quality_score: float,
    acceptable: bool = True,
    stability: float = 0.5,
    depth_report: DepthReport | None = None,
    metadata: dict | None = None,
) -> FrameCandidate:
    return FrameCandidate(
        frame_id=frame_id,
        rgb_image=_image(),
        timestamp=float(order),
        capture_order=order,
        source_id="mock",
        quality_report=_quality(quality_score, acceptable),
        depth_report=depth_report,
        stability_score=stability,
        metadata=metadata or {},
    )


def test_selects_clearly_best_candidate_from_deterministic_burst() -> None:
    result = select_best_frame(
        [
            _candidate("dark", order=0, quality_score=0.35, acceptable=False),
            _candidate("ok", order=1, quality_score=0.72, stability=0.6),
            _candidate("best", order=2, quality_score=0.92, stability=0.9),
        ]
    )

    assert result.success is True
    assert result.selected_frame is not None
    assert result.selected_frame.frame_id == "best"
    assert result.candidate_summaries[-1]["score_total"] > 0


def test_returns_no_acceptable_frame_with_recapture_guidance() -> None:
    result = select_best_frame(
        [
            _candidate("dark", order=0, quality_score=0.2, acceptable=False),
            _candidate("blurred", order=1, quality_score=0.3, acceptable=False),
        ]
    )

    assert result.success is False
    assert result.selected_frame is None
    assert result.error is not None
    assert result.error.error_code == CameraErrorCode.NO_ACCEPTABLE_FRAME
    assert "recapture" in result.guidance.lower()


def test_selection_is_deterministic_for_repeated_ordered_inputs() -> None:
    candidates = [
        _candidate("a", order=0, quality_score=0.75, stability=0.5),
        _candidate("b", order=1, quality_score=0.8, stability=0.5),
    ]

    selections = [select_best_frame(candidates).selected_frame.frame_id for _ in range(5)]

    assert selections == ["b", "b", "b", "b", "b"]


def test_tie_breaks_by_acceptable_quality_stability_then_earliest_order() -> None:
    higher_stability = select_best_frame(
        [
            _candidate("later", order=2, quality_score=0.8, stability=0.6),
            _candidate("steadier", order=1, quality_score=0.8, stability=0.9),
        ]
    )
    assert higher_stability.selected_frame.frame_id == "steadier"

    earliest = select_best_frame(
        [
            _candidate("first", order=0, quality_score=0.8, stability=0.7),
            _candidate("second", order=1, quality_score=0.8, stability=0.7),
        ]
    )
    assert earliest.selected_frame.frame_id == "first"


def test_rgb_only_candidates_use_neutral_distance_behavior() -> None:
    result = select_best_frame(
        [_candidate("rgb", order=0, quality_score=0.85, stability=0.7)]
    )

    assert result.success is True
    assert result.selected_frame.frame_score is not None
    assert result.selected_frame.frame_score.distance_score == 0.0
    assert result.candidate_summaries[0].get("distance_status") is None


def test_candidate_summaries_exclude_image_and_depth_payloads() -> None:
    depth = DepthReport(
        status=DistanceStatus.ACCEPTABLE,
        distance_cm=42.0,
        score_contribution=0.1,
        guidance="Distance is acceptable.",
    )
    result = select_best_frame(
        [
            _candidate(
                "safe",
                order=0,
                quality_score=0.9,
                depth_report=depth,
                metadata={
                    "rgb_image": _image(),
                    "depth_map": np.ones((8, 8)),
                    "source_type": CameraSourceType.MOCK.value,
                },
            )
        ]
    )

    summary = result.candidate_summaries[0]
    assert "rgb_image" not in summary
    assert "depth_map" not in summary
    assert summary["source_type"] == CameraSourceType.MOCK.value


def test_selector_preserves_distance_warning_when_depth_conflicts_with_quality() -> None:
    depth = DepthReport(
        status=DistanceStatus.TOO_CLOSE,
        distance_cm=20.0,
        score_contribution=-0.2,
        guidance="Move the document farther away.",
    )

    result = select_best_frame(
        [
            _candidate(
                "close-but-clear",
                order=0,
                quality_score=0.95,
                stability=0.8,
                depth_report=depth,
            )
        ]
    )

    assert result.success is True
    assert result.candidate_summaries[0]["distance_status"] == DistanceStatus.TOO_CLOSE.value
    assert result.candidate_summaries[0]["distance_cm"] == 20.0


def test_rgb_only_selection_succeeds_when_depth_is_unavailable() -> None:
    depth = DepthReport(
        status=DistanceStatus.UNAVAILABLE,
        distance_cm=None,
        score_contribution=0.0,
        guidance="Depth is unavailable; continuing with RGB capture.",
        reason="unsupported",
    )

    result = select_best_frame(
        [
            _candidate(
                "rgb-only",
                order=0,
                quality_score=0.88,
                stability=0.8,
                depth_report=depth,
            )
        ]
    )

    assert result.success is True
    assert result.selected_frame is not None
    assert result.candidate_summaries[0]["distance_status"] == DistanceStatus.UNAVAILABLE.value
