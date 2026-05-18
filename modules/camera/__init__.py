"""Camera capture and best-frame selection package."""

from modules.camera.camera_models import (
    BestFrameSelectionResult,
    CameraError,
    CameraErrorCode,
    CameraSourceType,
    CaptureBurstResult,
    CaptureFrameResult,
    CaptureRequest,
    CleanupStatus,
    DepthReport,
    DistanceStatus,
    FrameCandidate,
    FrameScore,
)
from modules.camera.depth_analyzer import analyze_depth
from modules.camera.frame_selector import score_candidate, select_best_frame
from modules.camera.orbbec_camera import (
    GenericRGBCameraSource,
    OrbbecDepthCameraSource,
    capture_burst_from_sources,
    default_camera_sources,
)

__all__ = [
    "BestFrameSelectionResult",
    "CameraError",
    "CameraErrorCode",
    "CameraSourceType",
    "CaptureBurstResult",
    "CaptureFrameResult",
    "CaptureRequest",
    "CleanupStatus",
    "DepthReport",
    "DistanceStatus",
    "FrameCandidate",
    "FrameScore",
    "GenericRGBCameraSource",
    "OrbbecDepthCameraSource",
    "analyze_depth",
    "capture_burst_from_sources",
    "default_camera_sources",
    "score_candidate",
    "select_best_frame",
]
