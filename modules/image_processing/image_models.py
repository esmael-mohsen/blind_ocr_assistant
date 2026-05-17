"""Image-processing request/result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray


ImageArray = NDArray[np.uint8]


class ImageProcessingErrorCode(StrEnum):
    """Stable image-processing failure codes for later spoken-message mapping."""

    IMAGE_INPUT_MISSING = "IMAGE_INPUT_MISSING"
    IMAGE_INPUT_UNREADABLE = "IMAGE_INPUT_UNREADABLE"
    IMAGE_UNSUPPORTED_FORMAT = "IMAGE_UNSUPPORTED_FORMAT"
    IMAGE_INVALID_DATA = "IMAGE_INVALID_DATA"
    IMAGE_TOO_DARK = "IMAGE_TOO_DARK"
    IMAGE_TOO_BRIGHT = "IMAGE_TOO_BRIGHT"
    IMAGE_TOO_BLURRY = "IMAGE_TOO_BLURRY"
    IMAGE_LOW_CONTRAST = "IMAGE_LOW_CONTRAST"
    IMAGE_TEXT_NOT_FOUND = "IMAGE_TEXT_NOT_FOUND"
    IMAGE_QUALITY_UNCERTAIN = "IMAGE_QUALITY_UNCERTAIN"
    IMAGE_PREPROCESSING_FAILED = "IMAGE_PREPROCESSING_FAILED"
    IMAGE_UNEXPECTED_ERROR = "IMAGE_UNEXPECTED_ERROR"


class OverallImageStatus(StrEnum):
    """Overall quality decision for the normal OCR path."""

    ACCEPTABLE = "acceptable"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


class QualityDimension(StrEnum):
    """Image quality dimensions evaluated in Phase 2."""

    BRIGHTNESS = "brightness"
    BLUR = "blur"
    CONTRAST = "contrast"
    TEXT_PRESENCE = "text_presence"


class BrightnessStatus(StrEnum):
    TOO_DARK = "too_dark"
    ACCEPTABLE = "acceptable"
    TOO_BRIGHT = "too_bright"


class BlurStatus(StrEnum):
    BLURRY = "blurry"
    ACCEPTABLE = "acceptable"


class ContrastStatus(StrEnum):
    LOW_CONTRAST = "low_contrast"
    ACCEPTABLE = "acceptable"


class TextPresenceStatus(StrEnum):
    LIKELY_TEXT = "likely_text"
    UNLIKELY_TEXT = "unlikely_text"
    UNCERTAIN_TEXT = "uncertain_text"


class GuidanceCategory(StrEnum):
    READY = "ready"
    IMPROVE_LIGHTING = "improve_lighting"
    HOLD_STEADY = "hold_steady"
    INCREASE_CONTRAST = "increase_contrast"
    POINT_TO_TEXT = "point_to_text"
    RECAPTURE = "recapture"
    INVALID_IMAGE = "invalid_image"


class PreprocessingVariantName(StrEnum):
    ONLINE_LIGHT = "online_light"
    LOCAL_NATURAL = "local_natural"
    EMERGENCY_STRONG = "emergency_strong"


class ImageProcessingException(ValueError):
    """Expected image-processing failure with a stable code."""

    def __init__(self, error_code: ImageProcessingErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


@dataclass(frozen=True)
class GuidanceMessage:
    """Short bilingual user guidance suitable for later TTS."""

    category: GuidanceCategory
    english_text: str
    arabic_text: str

    def __post_init__(self) -> None:
        if not self.english_text.strip() or not self.arabic_text.strip():
            raise ValueError("Guidance requires English and Arabic text")


@dataclass(frozen=True)
class QualityThresholds:
    """Configurable conservative thresholds for Phase 2 image decisions."""

    min_brightness: float = 45.0
    max_brightness: float = 235.0
    min_sharpness: float = 60.0
    min_contrast: float = 25.0
    min_text_presence: float = 0.12
    min_overall_score: float = 0.6

    def __post_init__(self) -> None:
        if self.min_brightness < 0 or self.max_brightness > 255:
            raise ValueError("brightness thresholds must be within 0..255")
        if self.min_brightness >= self.max_brightness:
            raise ValueError("min_brightness must be less than max_brightness")
        for name in (
            "min_sharpness",
            "min_contrast",
            "min_text_presence",
            "min_overall_score",
        ):
            value = getattr(self, name)
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.min_text_presence > 1 or self.min_overall_score > 1:
            raise ValueError("presence and overall score thresholds must be <= 1")


@dataclass(frozen=True)
class ImageInput:
    """One still image source for quality assessment or preprocessing."""

    image_path: str | Path | None = None
    image_bytes: bytes | None = None
    image_array: ImageArray | None = None
    source_id: str | None = None

    def __post_init__(self) -> None:
        sources = [
            self.image_path is not None,
            self.image_bytes is not None,
            self.image_array is not None,
        ]
        if sum(sources) != 1:
            raise ValueError("Exactly one image source is required")

    def decode(self) -> ImageArray:
        """Decode the configured image source into a copied BGR image array."""
        if self.image_array is not None:
            return _validate_image_array(self.image_array)
        if self.image_path is not None:
            path = Path(self.image_path)
            if not path.exists():
                raise ImageProcessingException(
                    ImageProcessingErrorCode.IMAGE_INPUT_UNREADABLE,
                    f"Image path does not exist: {path}",
                )
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if image is None:
                raise ImageProcessingException(
                    ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT,
                    f"Image path could not be decoded: {path}",
                )
            return _validate_image_array(image)
        if self.image_bytes is None or len(self.image_bytes) == 0:
            raise ImageProcessingException(
                ImageProcessingErrorCode.IMAGE_INPUT_MISSING,
                "Image bytes are empty.",
            )
        buffer = np.frombuffer(self.image_bytes, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageProcessingException(
                ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT,
                "Image bytes could not be decoded.",
            )
        return _validate_image_array(image)


@dataclass(frozen=True)
class QualityFinding:
    """Classified result for one image quality dimension."""

    dimension: QualityDimension
    status: StrEnum
    score: float
    message_key: GuidanceCategory

    def __post_init__(self) -> None:
        if self.score < 0:
            raise ValueError("quality finding score must be non-negative")


@dataclass(frozen=True)
class ImageQualityReport:
    """Structured image quality decision for the normal OCR path."""

    is_acceptable: bool
    overall_status: OverallImageStatus
    quality_score: float
    brightness_status: BrightnessStatus
    blur_status: BlurStatus
    contrast_status: ContrastStatus
    text_presence_status: TextPresenceStatus
    guidance: GuidanceMessage
    primary_issue: ImageProcessingErrorCode | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.quality_score < 0:
            raise ValueError("quality_score must be non-negative")
        if self.overall_status == OverallImageStatus.ACCEPTABLE and not self.is_acceptable:
            raise ValueError("acceptable status requires is_acceptable=True")
        if self.overall_status != OverallImageStatus.ACCEPTABLE and self.is_acceptable:
            raise ValueError("rejected or uncertain status requires is_acceptable=False")
        if not self.is_acceptable and self.primary_issue is None:
            raise ValueError("rejected or uncertain reports require primary_issue")


@dataclass(frozen=True)
class VariantResult:
    """One preprocessing variant or structured variant failure."""

    name: PreprocessingVariantName
    image: ImageArray | None = None
    success: bool = True
    error_code: ImageProcessingErrorCode | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.success and self.image is None:
            raise ValueError("successful variant requires image")
        if not self.success and (self.error_code is None or not self.error_message):
            raise ValueError("failed variant requires error details")


@dataclass(frozen=True)
class PreprocessingVariantSet:
    """Named OCR-preparation variants for a single source image."""

    source_id: str | None
    original_preserved: bool
    variants: dict[PreprocessingVariantName, VariantResult]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        missing = set(PreprocessingVariantName).difference(self.variants)
        if missing:
            raise ValueError(f"Missing preprocessing variants: {sorted(m.value for m in missing)}")
        if not self.original_preserved:
            raise ValueError("preprocessing must preserve the original image")


def _validate_image_array(image: ImageArray) -> ImageArray:
    if not isinstance(image, np.ndarray):
        raise ImageProcessingException(
            ImageProcessingErrorCode.IMAGE_INVALID_DATA,
            "Image array must be a numpy array.",
        )
    if image.size == 0 or image.ndim not in {2, 3}:
        raise ImageProcessingException(
            ImageProcessingErrorCode.IMAGE_INVALID_DATA,
            "Image array must have positive dimensions.",
        )
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[0] <= 0 or image.shape[1] <= 0:
        raise ImageProcessingException(
            ImageProcessingErrorCode.IMAGE_INVALID_DATA,
            "Image array must have positive width and height.",
        )
    return image.copy()


def safe_image_metadata(
    *,
    source_id: str | None = None,
    image: ImageArray | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return metadata safe for default logs, excluding image/text contents."""
    safe: dict[str, Any] = {}
    if source_id:
        safe["source_id"] = source_id
    if image is not None:
        safe["image_width"] = int(image.shape[1])
        safe["image_height"] = int(image.shape[0])
    blocked = {
        "image",
        "image_array",
        "image_bytes",
        "raw_image",
        "raw_text",
        "clean_text",
        "ocr_text",
        "text",
        "debug_path",
        "artifact_path",
    }
    for key, value in (metadata or {}).items():
        if key in blocked:
            continue
        if isinstance(value, (bytes, bytearray, np.ndarray)):
            continue
        safe[key] = value
    return safe


def image_log_metadata(
    report: ImageQualityReport | PreprocessingVariantSet,
) -> dict[str, Any]:
    """Return log-safe metadata for image-processing results."""
    metadata = dict(report.metadata)
    if isinstance(report, ImageQualityReport):
        metadata.update(
            {
                "is_acceptable": report.is_acceptable,
                "overall_status": report.overall_status.value,
                "quality_score": report.quality_score,
                "brightness_status": report.brightness_status.value,
                "blur_status": report.blur_status.value,
                "contrast_status": report.contrast_status.value,
                "text_presence_status": report.text_presence_status.value,
                "guidance_category": report.guidance.category.value,
            }
        )
        if report.primary_issue is not None:
            metadata["error_code"] = report.primary_issue.value
    else:
        metadata.update(
            {
                "source_id": report.source_id,
                "original_preserved": report.original_preserved,
                "variant_names": [name.value for name in report.variants],
            }
        )
    return safe_image_metadata(metadata=metadata)
