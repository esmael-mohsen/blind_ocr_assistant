"""Depth distance analysis for Phase 3 camera guidance."""

from __future__ import annotations

from typing import Any

import numpy as np

from config import DEFAULT_CAMERA_DEPTH_TOO_CLOSE_CM, DEFAULT_CAMERA_DEPTH_TOO_FAR_CM
from modules.camera.camera_models import DepthReport, DistanceStatus


TOO_CLOSE_SCORE = -0.2
ACCEPTABLE_SCORE = 0.1
TOO_FAR_SCORE = -0.2
UNAVAILABLE_SCORE = 0.0


def analyze_depth(depth_map: Any, rgb_shape: tuple[int, ...] | None = None) -> DepthReport:
    """Classify document distance from an optional depth map."""
    if not isinstance(depth_map, np.ndarray) or depth_map.size == 0:
        return _unavailable("missing_or_unsupported")
    if rgb_shape is not None and len(rgb_shape) >= 2:
        if depth_map.shape[0] != rgb_shape[0] or depth_map.shape[1] != rgb_shape[1]:
            return _unavailable("unaligned")

    depth = depth_map.astype(float, copy=False)
    valid = depth[np.isfinite(depth) & (depth > 0)]
    if valid.size == 0:
        return _unavailable("invalid_or_noisy")

    distance_cm = round(float(np.median(valid)), 3)
    if distance_cm < DEFAULT_CAMERA_DEPTH_TOO_CLOSE_CM:
        return DepthReport(
            status=DistanceStatus.TOO_CLOSE,
            distance_cm=distance_cm,
            score_contribution=TOO_CLOSE_SCORE,
            guidance="Move the document farther from the camera.",
        )
    if distance_cm > DEFAULT_CAMERA_DEPTH_TOO_FAR_CM:
        return DepthReport(
            status=DistanceStatus.TOO_FAR,
            distance_cm=distance_cm,
            score_contribution=TOO_FAR_SCORE,
            guidance="Move the document closer to the camera.",
        )
    return DepthReport(
        status=DistanceStatus.ACCEPTABLE,
        distance_cm=distance_cm,
        score_contribution=ACCEPTABLE_SCORE,
        guidance="Document distance is acceptable.",
    )


def _unavailable(reason: str) -> DepthReport:
    return DepthReport(
        status=DistanceStatus.UNAVAILABLE,
        distance_cm=None,
        score_contribution=UNAVAILABLE_SCORE,
        guidance="Depth is unavailable; continuing with RGB capture.",
        reason=reason,
    )
