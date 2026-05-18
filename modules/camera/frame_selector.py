"""Deterministic best-frame selection for Phase 3."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from modules.camera.camera_models import (
    BestFrameSelectionResult,
    CameraError,
    CameraErrorCode,
    CameraSourceType,
    CleanupStatus,
    FrameCandidate,
    FrameScore,
)
from modules.camera.depth_analyzer import analyze_depth
from modules.image_processing.image_models import ImageInput
from modules.image_processing.quality_checker import assess_image_quality


QUALITY_WEIGHT = 0.75
STABILITY_WEIGHT = 0.15
DISTANCE_WEIGHT = 0.10
NO_ACCEPTABLE_GUIDANCE = "Recapture the image more clearly."


def select_best_frame(
    candidates: list[FrameCandidate],
    *,
    source_type: CameraSourceType = CameraSourceType.MOCK,
    partial_timeout: bool = False,
    cleanup_status: CleanupStatus = CleanupStatus.NOT_REQUIRED,
) -> BestFrameSelectionResult:
    """Select the highest-scoring acceptable frame from an ordered burst."""
    scored = [_score_candidate(candidate) for candidate in candidates]
    summaries = [candidate.safe_summary() for candidate in scored]
    acceptable = [
        candidate
        for candidate in scored
        if candidate.frame_score is not None and candidate.frame_score.quality_acceptable
    ]
    if not acceptable:
        return BestFrameSelectionResult(
            success=False,
            selected_frame=None,
            candidate_summaries=summaries,
            guidance=_recapture_guidance(scored),
            source_type=source_type,
            partial_timeout=partial_timeout,
            error=CameraError(
                error_code=CameraErrorCode.NO_ACCEPTABLE_FRAME,
                message="No acceptable frame was found in the capture burst.",
                guidance=NO_ACCEPTABLE_GUIDANCE,
            ),
            cleanup_status=cleanup_status,
        )

    selected = max(
        acceptable,
        key=lambda candidate: (
            round(candidate.frame_score.total_score, 6),
            candidate.frame_score.tie_quality_rank,
            round(candidate.frame_score.tie_stability_rank, 6),
            -candidate.frame_score.tie_order_rank,
        ),
    )
    return BestFrameSelectionResult(
        success=True,
        selected_frame=selected,
        candidate_summaries=summaries,
        guidance="The image is ready for reading.",
        source_type=source_type,
        partial_timeout=partial_timeout,
        cleanup_status=cleanup_status,
    )


def score_candidate(candidate: FrameCandidate) -> FrameCandidate:
    """Return a copy of a frame candidate with Phase 3 score fields populated."""
    return _score_candidate(candidate)


def _score_candidate(candidate: FrameCandidate) -> FrameCandidate:
    depth_report = candidate.depth_report
    if depth_report is None and candidate.depth_map is not None:
        depth_report = analyze_depth(candidate.depth_map, candidate.rgb_image.shape)
        candidate = replace(candidate, depth_report=depth_report)
    quality_score, quality_acceptable = _quality_values(candidate)
    stability_score = _clamp_score(
        _metadata_float(candidate.metadata, "stability_score", candidate.stability_score)
    )
    distance_score = _distance_score(candidate)
    total_score = max(
        0.0,
        (quality_score * QUALITY_WEIGHT)
        + (stability_score * STABILITY_WEIGHT)
        + (distance_score * DISTANCE_WEIGHT),
    )
    frame_score = FrameScore(
        quality_score=quality_score,
        quality_acceptable=quality_acceptable,
        stability_score=stability_score,
        distance_score=distance_score,
        total_score=total_score,
        tie_quality_rank=1 if quality_acceptable else 0,
        tie_stability_rank=stability_score,
        tie_order_rank=candidate.capture_order,
    )
    return replace(
        candidate,
        frame_score=frame_score,
        stability_score=stability_score,
        distance_score=distance_score,
        total_score=total_score,
    )


def _quality_values(candidate: FrameCandidate) -> tuple[float, bool]:
    report = candidate.quality_report
    if report is None:
        report = assess_image_quality(
            ImageInput(image_array=candidate.rgb_image, source_id=candidate.frame_id)
        )
    score = _clamp_score(float(getattr(report, "quality_score", 0.0)))
    acceptable = bool(getattr(report, "is_acceptable", False))
    return score, acceptable


def _distance_score(candidate: FrameCandidate) -> float:
    if candidate.depth_report is None:
        return 0.0
    return float(candidate.depth_report.score_contribution)


def _recapture_guidance(candidates: list[FrameCandidate]) -> str:
    for candidate in candidates:
        report = candidate.quality_report
        guidance = getattr(report, "guidance", None)
        english = getattr(guidance, "english_text", None)
        if isinstance(english, str) and english.strip():
            return english
    return NO_ACCEPTABLE_GUIDANCE


def _metadata_float(metadata: dict[str, Any], key: str, default: float) -> float:
    value = metadata.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))
