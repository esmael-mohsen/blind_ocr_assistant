"""Structured camera models for Phase 3 capture and frame selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np
from numpy.typing import NDArray

from config import (
    DEFAULT_CAMERA_CAPTURE_TIMEOUT_SECONDS,
    DEFAULT_CAMERA_FRAME_CAPTURE_COUNT,
    MAX_CAMERA_FRAME_CAPTURE_COUNT,
    MIN_CAMERA_FRAME_CAPTURE_COUNT,
)


ImageArray = NDArray[np.uint8]
DepthArray = NDArray[Any]


class CameraSourceType(StrEnum):
    """Camera source categories supported by Phase 3."""

    TARGET_DEPTH = "target_depth"
    GENERIC_RGB = "generic_rgb"
    MOCK = "mock"


class DistanceStatus(StrEnum):
    """Depth-derived document distance status."""

    TOO_CLOSE = "too_close"
    ACCEPTABLE = "acceptable"
    TOO_FAR = "too_far"
    UNAVAILABLE = "unavailable"


class CleanupStatus(StrEnum):
    """Camera resource cleanup outcome."""

    RELEASED = "released"
    RELEASE_FAILED = "release_failed"
    NOT_REQUIRED = "not_required"


class CameraErrorCode(StrEnum):
    """Stable Phase 3 camera and frame-selection failure codes."""

    CAMERA_OPEN_FAILED = "CAMERA_OPEN_FAILED"
    CAMERA_CAPTURE_TIMEOUT = "CAMERA_CAPTURE_TIMEOUT"
    CAMERA_EMPTY_FRAME = "CAMERA_EMPTY_FRAME"
    CAMERA_INVALID_FRAME = "CAMERA_INVALID_FRAME"
    CAMERA_DEPTH_UNAVAILABLE = "CAMERA_DEPTH_UNAVAILABLE"
    NO_ACCEPTABLE_FRAME = "NO_ACCEPTABLE_FRAME"
    CAMERA_RESOURCE_RELEASE_FAILED = "CAMERA_RESOURCE_RELEASE_FAILED"
    CAMERA_UNEXPECTED_ERROR = "CAMERA_UNEXPECTED_ERROR"


SENSITIVE_METADATA_KEYS = {
    "artifact_path",
    "clean_text",
    "debug_path",
    "depth",
    "depth_map",
    "image",
    "image_array",
    "image_bytes",
    "ocr_text",
    "password",
    "raw_image",
    "raw_text",
    "secret",
    "text",
    "token",
}


def sanitize_camera_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return metadata safe for default logs and result summaries."""
    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key in SENSITIVE_METADATA_KEYS:
            continue
        if isinstance(value, (bytes, bytearray, np.ndarray)):
            continue
        if isinstance(value, StrEnum):
            safe[key] = value.value
        else:
            safe[key] = value
    return safe


def image_dimensions_metadata(image: ImageArray | None) -> dict[str, int]:
    """Return safe width and height metadata for an image array."""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {}
    if image.ndim < 2:
        return {}
    return {"image_width": int(image.shape[1]), "image_height": int(image.shape[0])}


@dataclass(frozen=True)
class CaptureRequest:
    """A bounded RGB/depth capture request."""

    requested_count: int | None = None
    timeout_seconds: float = DEFAULT_CAMERA_CAPTURE_TIMEOUT_SECONDS
    prefer_depth: bool = True
    allow_rgb_fallback: bool = True
    debug_save_enabled: bool = False
    capture_count: int = field(init=False)

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        requested = (
            DEFAULT_CAMERA_FRAME_CAPTURE_COUNT
            if self.requested_count is None
            else int(self.requested_count)
        )
        clamped = max(
            MIN_CAMERA_FRAME_CAPTURE_COUNT,
            min(MAX_CAMERA_FRAME_CAPTURE_COUNT, requested),
        )
        object.__setattr__(self, "capture_count", clamped)


@dataclass(frozen=True)
class CameraError:
    """Expected camera failure with a stable code and safe message."""

    error_code: CameraErrorCode
    message: str
    guidance: str | None = None

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("camera error message is required")


@dataclass(frozen=True)
class DepthReport:
    """Depth distance report for a frame candidate."""

    status: DistanceStatus
    distance_cm: float | None = None
    score_contribution: float = 0.0
    guidance: str = "Depth is unavailable; continuing with RGB capture."
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.distance_cm is not None and self.distance_cm < 0:
            raise ValueError("distance_cm must be non-negative")
        if not self.guidance.strip():
            raise ValueError("depth guidance is required")


@dataclass(frozen=True)
class FrameScore:
    """Deterministic score breakdown for one frame candidate."""

    quality_score: float
    quality_acceptable: bool
    stability_score: float
    distance_score: float
    total_score: float
    tie_quality_rank: int
    tie_stability_rank: float
    tie_order_rank: int

    def __post_init__(self) -> None:
        for name in (
            "quality_score",
            "stability_score",
            "total_score",
            "tie_stability_rank",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.tie_order_rank < 0:
            raise ValueError("tie_order_rank must be non-negative")


@dataclass(frozen=True)
class FrameCandidate:
    """One captured or synthetic frame eligible for selection."""

    frame_id: str
    rgb_image: ImageArray
    timestamp: float
    capture_order: int
    source_id: str
    depth_map: DepthArray | None = None
    quality_report: Any | None = None
    depth_report: DepthReport | None = None
    frame_score: FrameScore | None = None
    stability_score: float = 0.0
    distance_score: float = 0.0
    total_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frame_id.strip():
            raise ValueError("frame_id is required")
        if self.capture_order < 0:
            raise ValueError("capture_order must be non-negative")
        validated = validate_rgb_image(self.rgb_image)
        metadata = sanitize_camera_metadata(self.metadata)
        metadata.update(image_dimensions_metadata(validated))
        metadata.setdefault("source_id", self.source_id)
        object.__setattr__(self, "rgb_image", validated)
        object.__setattr__(self, "metadata", metadata)

    def safe_summary(self) -> dict[str, Any]:
        """Return a log-safe summary excluding image and depth payloads."""
        summary = {
            "frame_id": self.frame_id,
            "capture_order": self.capture_order,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "stability_score": self.stability_score,
            "distance_score": self.distance_score,
            "total_score": self.total_score,
        }
        if self.frame_score is not None:
            summary.update(
                {
                    "quality_score": self.frame_score.quality_score,
                    "quality_acceptable": self.frame_score.quality_acceptable,
                    "score_total": self.frame_score.total_score,
                }
            )
        if self.depth_report is not None:
            summary.update(
                {
                    "distance_status": self.depth_report.status.value,
                    "distance_cm": self.depth_report.distance_cm,
                }
            )
        summary.update(self.metadata)
        return sanitize_camera_metadata(summary)


@dataclass(frozen=True)
class CaptureFrameResult:
    """Result from attempting to capture one frame."""

    success: bool
    candidate: FrameCandidate | None = None
    error: CameraError | None = None

    def __post_init__(self) -> None:
        if self.success and self.candidate is None:
            raise ValueError("successful frame capture requires candidate")
        if not self.success and self.error is None:
            raise ValueError("failed frame capture requires error")


@dataclass(frozen=True)
class CaptureBurstResult:
    """Structured result from attempting a bounded capture burst."""

    success: bool
    candidates: list[FrameCandidate]
    source_type: CameraSourceType
    partial_timeout: bool = False
    error: CameraError | None = None
    message: str = ""
    cleanup_status: CleanupStatus = CleanupStatus.RELEASED
    selection_result: BestFrameSelectionResult | None = None

    def __post_init__(self) -> None:
        if self.success and not self.candidates:
            raise ValueError("successful capture requires at least one candidate")
        if not self.success and self.error is None:
            raise ValueError("failed capture requires error")


@dataclass(frozen=True)
class BestFrameSelectionResult:
    """Best-frame selection outcome for one burst."""

    success: bool
    selected_frame: FrameCandidate | None
    candidate_summaries: list[dict[str, Any]]
    guidance: str
    source_type: CameraSourceType
    partial_timeout: bool = False
    error: CameraError | None = None
    cleanup_status: CleanupStatus = CleanupStatus.NOT_REQUIRED

    def __post_init__(self) -> None:
        if self.success and self.selected_frame is None:
            raise ValueError("successful selection requires selected_frame")
        if not self.success and self.error is None:
            raise ValueError("failed selection requires error")
        if not self.guidance.strip():
            raise ValueError("selection guidance is required")
        safe_summaries = [
            sanitize_camera_metadata(summary) for summary in self.candidate_summaries
        ]
        object.__setattr__(self, "candidate_summaries", safe_summaries)


def validate_rgb_image(image: ImageArray) -> ImageArray:
    """Validate and normalize one RGB/BGR image array without mutating input."""
    if not isinstance(image, np.ndarray):
        raise ValueError("rgb_image must be a numpy array")
    if image.size == 0 or image.ndim not in {2, 3}:
        raise ValueError("rgb_image must have positive 2D or 3D dimensions")
    if image.ndim == 3 and image.shape[2] not in {1, 3, 4}:
        raise ValueError("rgb_image channel count must be 1, 3, or 4")
    if image.shape[0] <= 0 or image.shape[1] <= 0:
        raise ValueError("rgb_image must have positive width and height")
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return image.copy()


def camera_log_metadata(
    result: BestFrameSelectionResult | CaptureBurstResult,
) -> dict[str, Any]:
    """Return safe default metadata for camera logs."""
    metadata: dict[str, Any] = {
        "success": result.success,
        "source_type": result.source_type.value,
        "partial_timeout": result.partial_timeout,
        "cleanup_status": result.cleanup_status.value,
    }
    if isinstance(result, BestFrameSelectionResult):
        metadata["candidate_count"] = len(result.candidate_summaries)
        if result.selected_frame is not None:
            metadata["selected_frame_id"] = result.selected_frame.frame_id
    else:
        metadata["candidate_count"] = len(result.candidates)
    if result.error is not None:
        metadata["error_code"] = result.error.error_code.value
    return sanitize_camera_metadata(metadata)
