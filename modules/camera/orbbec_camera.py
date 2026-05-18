"""Camera adapter boundary for Orbbec-first RGB/depth capture."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from modules.camera.camera_models import (
    CameraError,
    CameraErrorCode,
    CameraSourceType,
    CaptureBurstResult,
    CaptureRequest,
    CleanupStatus,
    DepthArray,
    FrameCandidate,
    ImageArray,
    validate_rgb_image,
)
from modules.camera.depth_analyzer import analyze_depth
from modules.camera.frame_selector import select_best_frame
from modules.image_processing.image_models import ImageInput
from modules.image_processing.quality_checker import assess_image_quality


class CameraSource(Protocol):
    """Minimal camera source protocol used by capture orchestration."""

    source_id: str
    source_type: CameraSourceType
    supports_rgb: bool
    supports_depth: bool

    def open(self) -> bool: ...

    def capture_frame(self) -> object: ...

    def release(self) -> None: ...


@dataclass
class OrbbecDepthCameraSource:
    """Target depth camera adapter boundary.

    The concrete SDK dependency is intentionally optional. When an SDK-backed
    source is not supplied later, this source reports unavailable safely so tests
    and development machines do not require Orbbec libraries.
    """

    source_id: str = "orbbec-astra-pro"
    source_type: CameraSourceType = CameraSourceType.TARGET_DEPTH
    supports_rgb: bool = True
    supports_depth: bool = True

    def open(self) -> bool:
        return False

    def capture_frame(self) -> object:
        raise RuntimeError("Orbbec SDK or OpenNI2 adapter is not configured")

    def release(self) -> None:
        return None


class GenericRGBCameraSource:
    """Generic OpenCV RGB capture fallback."""

    source_type = CameraSourceType.GENERIC_RGB
    supports_rgb = True
    supports_depth = False

    def __init__(self, camera_index: int = 0, source_id: str = "opencv-rgb-0") -> None:
        self.camera_index = camera_index
        self.source_id = source_id
        self._capture: Any | None = None

    def open(self) -> bool:
        try:
            import cv2
        except ImportError:
            return False
        self._capture = cv2.VideoCapture(self.camera_index)
        return bool(self._capture is not None and self._capture.isOpened())

    def capture_frame(self) -> object:
        if self._capture is None:
            raise RuntimeError("camera source is not open")
        ok, frame = self._capture.read()
        if not ok:
            raise RuntimeError("camera returned no RGB frame")
        return frame

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None


def default_camera_sources() -> list[CameraSource]:
    """Return the default Orbbec-first source list."""
    return [OrbbecDepthCameraSource(), GenericRGBCameraSource()]


def capture_burst_from_sources(
    sources: list[CameraSource],
    request: CaptureRequest,
) -> CaptureBurstResult:
    """Capture one bounded burst from the first available camera source."""
    ordered_sources = _ordered_sources(sources, request)
    last_error: CameraError | None = None
    for source in ordered_sources:
        opened = False
        cleanup_status = CleanupStatus.RELEASED
        try:
            opened = bool(source.open())
            if not opened:
                last_error = CameraError(
                    CameraErrorCode.CAMERA_OPEN_FAILED,
                    f"Camera source {source.source_id} could not be opened.",
                    "Camera is unavailable. Try again.",
                )
                continue
            return _capture_from_open_source(source, request)
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            last_error = CameraError(
                CameraErrorCode.CAMERA_UNEXPECTED_ERROR,
                f"Unexpected camera failure: {exc}",
                "Camera capture failed. Try again.",
            )
        finally:
            if not opened and last_error is not None:
                cleanup_status = _release_once(source)
        if cleanup_status == CleanupStatus.RELEASE_FAILED:
            last_error = CameraError(
                CameraErrorCode.CAMERA_RESOURCE_RELEASE_FAILED,
                f"Camera source {source.source_id} failed to release.",
                "Camera cleanup failed. Restart the camera and try again.",
            )
        if opened:
            return _failure_result(
                source.source_type,
                last_error or CameraError(
                    CameraErrorCode.CAMERA_UNEXPECTED_ERROR,
                    "Camera capture failed.",
                ),
                cleanup_status,
            )
    return _failure_result(
        CameraSourceType.GENERIC_RGB,
        last_error
        or CameraError(
            CameraErrorCode.CAMERA_OPEN_FAILED,
            "No camera source could be opened.",
            "Camera is unavailable. Try again.",
        ),
        CleanupStatus.RELEASED,
    )


def _capture_from_open_source(
    source: CameraSource,
    request: CaptureRequest,
) -> CaptureBurstResult:
    candidates: list[FrameCandidate] = []
    first_error: CameraError | None = None
    partial_timeout = False
    cleanup_status = CleanupStatus.RELEASED
    try:
        start = time.monotonic()
        for index in range(request.capture_count):
            if time.monotonic() - start > request.timeout_seconds:
                partial_timeout = True
                break
            try:
                frame = source.capture_frame()
                candidate = _frame_to_candidate(source, frame, index)
                candidates.append(candidate)
            except TimeoutError:
                partial_timeout = True
                break
            except ValueError as exc:
                first_error = _frame_error(exc)
                continue
            except KeyboardInterrupt:
                raise
            except BaseException as exc:
                first_error = CameraError(
                    CameraErrorCode.CAMERA_UNEXPECTED_ERROR,
                    f"Camera capture failed: {exc}",
                    "Camera capture failed. Try again.",
                )
                break
    finally:
        cleanup_status = _release_once(source)

    if candidates:
        selection = select_best_frame(
            candidates,
            source_type=source.source_type,
            partial_timeout=partial_timeout,
            cleanup_status=cleanup_status,
        )
        return CaptureBurstResult(
            success=True,
            candidates=candidates,
            source_type=source.source_type,
            partial_timeout=partial_timeout,
            message="Captured valid frame candidates.",
            cleanup_status=cleanup_status,
            selection_result=selection,
        )
    if partial_timeout and first_error is None:
        first_error = CameraError(
            CameraErrorCode.CAMERA_CAPTURE_TIMEOUT,
            "Capture timed out before any valid frame was captured.",
            "Camera timed out. Try again.",
        )
    return _failure_result(
        source.source_type,
        first_error
        or CameraError(
            CameraErrorCode.CAMERA_CAPTURE_TIMEOUT,
            "No valid frame was captured.",
            "Camera timed out. Try again.",
        ),
        cleanup_status,
    )


def _frame_to_candidate(
    source: CameraSource,
    frame: object,
    index: int,
) -> FrameCandidate:
    rgb_image, depth_map, metadata = _unpack_frame(frame)
    validated = validate_rgb_image(rgb_image)
    quality_report = assess_image_quality(
        ImageInput(image_array=validated, source_id=f"{source.source_id}-{index}")
    )
    metadata = {
        **metadata,
        "source_type": source.source_type.value,
        "supports_depth": source.supports_depth,
    }
    return FrameCandidate(
        frame_id=f"{source.source_id}-{index}",
        rgb_image=validated,
        depth_map=depth_map,
        timestamp=time.time(),
        capture_order=index,
        source_id=source.source_id,
        quality_report=quality_report,
        depth_report=analyze_depth(depth_map, validated.shape) if depth_map is not None else None,
        metadata=metadata,
    )


def _unpack_frame(frame: object) -> tuple[ImageArray, DepthArray | None, dict[str, Any]]:
    if isinstance(frame, dict):
        rgb = frame.get("rgb_image", frame.get("rgb"))
        depth = frame.get("depth_map", frame.get("depth"))
        metadata = dict(frame.get("metadata", {}))
    elif isinstance(frame, tuple):
        rgb = frame[0] if len(frame) >= 1 else None
        depth = frame[1] if len(frame) >= 2 else None
        metadata = frame[2] if len(frame) >= 3 and isinstance(frame[2], dict) else {}
    else:
        rgb = frame
        depth = None
        metadata = {}
    if not isinstance(rgb, np.ndarray):
        raise ValueError("invalid frame")
    if rgb.size == 0:
        raise ValueError("empty frame")
    return rgb, depth if isinstance(depth, np.ndarray) else None, metadata


def _frame_error(exc: ValueError) -> CameraError:
    message = str(exc)
    if "empty" in message or "positive" in message:
        return CameraError(
            CameraErrorCode.CAMERA_EMPTY_FRAME,
            "Camera returned an empty frame.",
            "Camera returned no image. Try again.",
        )
    return CameraError(
        CameraErrorCode.CAMERA_INVALID_FRAME,
        "Camera returned an invalid frame.",
        "Camera returned an unreadable image. Try again.",
    )


def _ordered_sources(
    sources: list[CameraSource],
    request: CaptureRequest,
) -> list[CameraSource]:
    if not request.prefer_depth:
        return list(sources)
    return sorted(
        sources,
        key=lambda source: 0
        if source.source_type == CameraSourceType.TARGET_DEPTH
        else 1,
    )


def _release_once(source: CameraSource) -> CleanupStatus:
    try:
        source.release()
    except BaseException:
        return CleanupStatus.RELEASE_FAILED
    return CleanupStatus.RELEASED


def _failure_result(
    source_type: CameraSourceType,
    error: CameraError,
    cleanup_status: CleanupStatus,
) -> CaptureBurstResult:
    return CaptureBurstResult(
        success=False,
        candidates=[],
        source_type=source_type,
        partial_timeout=error.error_code == CameraErrorCode.CAMERA_CAPTURE_TIMEOUT,
        error=error,
        message=error.message,
        cleanup_status=cleanup_status,
    )
