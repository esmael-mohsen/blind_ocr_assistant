"""Local image quality checks and bilingual guidance."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from modules.image_processing.image_models import (
    BrightnessStatus,
    BlurStatus,
    ContrastStatus,
    GuidanceCategory,
    GuidanceMessage,
    ImageInput,
    ImageProcessingErrorCode,
    ImageQualityReport,
    OverallImageStatus,
    QualityDimension,
    QualityFinding,
    QualityThresholds,
    TextPresenceStatus,
    safe_image_metadata,
)
from modules.image_processing.text_region_detector import estimate_text_presence_from_image


GUIDANCE_CATALOG: dict[GuidanceCategory, GuidanceMessage] = {
    GuidanceCategory.READY: GuidanceMessage(
        category=GuidanceCategory.READY,
        english_text="The image is ready for reading.",
        arabic_text="الصورة جاهزة للقراءة.",
    ),
    GuidanceCategory.IMPROVE_LIGHTING: GuidanceMessage(
        category=GuidanceCategory.IMPROVE_LIGHTING,
        english_text="Improve the lighting and try again.",
        arabic_text="حسن الإضاءة وحاول مرة أخرى.",
    ),
    GuidanceCategory.HOLD_STEADY: GuidanceMessage(
        category=GuidanceCategory.HOLD_STEADY,
        english_text="Hold the camera steady and recapture.",
        arabic_text="ثبت الكاميرا وأعد الالتقاط.",
    ),
    GuidanceCategory.INCREASE_CONTRAST: GuidanceMessage(
        category=GuidanceCategory.INCREASE_CONTRAST,
        english_text="Move to clearer contrast and try again.",
        arabic_text="حاول في مكان أوضح تباينا.",
    ),
    GuidanceCategory.POINT_TO_TEXT: GuidanceMessage(
        category=GuidanceCategory.POINT_TO_TEXT,
        english_text="Point the camera toward printed text.",
        arabic_text="وجه الكاميرا نحو النص المطبوع.",
    ),
    GuidanceCategory.RECAPTURE: GuidanceMessage(
        category=GuidanceCategory.RECAPTURE,
        english_text="Recapture the image more clearly.",
        arabic_text="أعد التقاط الصورة بوضوح أكبر.",
    ),
    GuidanceCategory.INVALID_IMAGE: GuidanceMessage(
        category=GuidanceCategory.INVALID_IMAGE,
        english_text="The image could not be read. Try another capture.",
        arabic_text="تعذر قراءة الصورة. حاول التقاط صورة أخرى.",
    ),
}


ISSUE_GUIDANCE: dict[ImageProcessingErrorCode, GuidanceCategory] = {
    ImageProcessingErrorCode.IMAGE_TOO_DARK: GuidanceCategory.IMPROVE_LIGHTING,
    ImageProcessingErrorCode.IMAGE_TOO_BRIGHT: GuidanceCategory.IMPROVE_LIGHTING,
    ImageProcessingErrorCode.IMAGE_TOO_BLURRY: GuidanceCategory.HOLD_STEADY,
    ImageProcessingErrorCode.IMAGE_LOW_CONTRAST: GuidanceCategory.INCREASE_CONTRAST,
    ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND: GuidanceCategory.POINT_TO_TEXT,
    ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN: GuidanceCategory.RECAPTURE,
    ImageProcessingErrorCode.IMAGE_INPUT_MISSING: GuidanceCategory.INVALID_IMAGE,
    ImageProcessingErrorCode.IMAGE_INPUT_UNREADABLE: GuidanceCategory.INVALID_IMAGE,
    ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT: GuidanceCategory.INVALID_IMAGE,
    ImageProcessingErrorCode.IMAGE_INVALID_DATA: GuidanceCategory.INVALID_IMAGE,
}


ISSUE_PRIORITY = (
    ImageProcessingErrorCode.IMAGE_INPUT_MISSING,
    ImageProcessingErrorCode.IMAGE_INPUT_UNREADABLE,
    ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT,
    ImageProcessingErrorCode.IMAGE_INVALID_DATA,
    ImageProcessingErrorCode.IMAGE_TOO_DARK,
    ImageProcessingErrorCode.IMAGE_TOO_BRIGHT,
    ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND,
    ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN,
    ImageProcessingErrorCode.IMAGE_LOW_CONTRAST,
    ImageProcessingErrorCode.IMAGE_TOO_BLURRY,
)


def get_guidance(category: GuidanceCategory) -> GuidanceMessage:
    """Return a bilingual guidance message by category."""
    return GUIDANCE_CATALOG[category]


def guidance_for_issue(issue: ImageProcessingErrorCode | None) -> GuidanceMessage:
    """Return the primary bilingual guidance for a quality issue."""
    if issue is None:
        return get_guidance(GuidanceCategory.READY)
    return get_guidance(ISSUE_GUIDANCE.get(issue, GuidanceCategory.RECAPTURE))


def choose_primary_issue(
    issues: list[ImageProcessingErrorCode],
) -> ImageProcessingErrorCode | None:
    """Choose the most actionable issue using a stable priority order."""
    if not issues:
        return None
    for issue in ISSUE_PRIORITY:
        if issue in issues:
            return issue
    return issues[0]


def classify_brightness(
    image: NDArray[np.uint8],
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Classify image lighting using a stable named category."""
    thresholds = thresholds or QualityThresholds()
    gray = _to_gray(image)
    mean = float(np.mean(gray))
    if mean < thresholds.min_brightness:
        status = BrightnessStatus.TOO_DARK
        score = mean / max(thresholds.min_brightness, 1)
        message_key = GuidanceCategory.IMPROVE_LIGHTING
    elif mean > thresholds.max_brightness:
        status = BrightnessStatus.TOO_BRIGHT
        score = max(0.0, (255.0 - mean) / max(255.0 - thresholds.max_brightness, 1))
        message_key = GuidanceCategory.IMPROVE_LIGHTING
    else:
        status = BrightnessStatus.ACCEPTABLE
        center = (thresholds.min_brightness + thresholds.max_brightness) / 2
        span = (thresholds.max_brightness - thresholds.min_brightness) / 2
        score = 1.0 - min(1.0, abs(mean - center) / max(span, 1))
        message_key = GuidanceCategory.READY
    return QualityFinding(
        dimension=QualityDimension.BRIGHTNESS,
        status=status,
        score=max(0.0, min(1.0, score)),
        message_key=message_key,
    )


def classify_blur(
    image: NDArray[np.uint8],
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Classify sharpness using Laplacian variance."""
    thresholds = thresholds or QualityThresholds()
    variance = float(cv2.Laplacian(_to_gray(image), cv2.CV_64F).var())
    if variance < thresholds.min_sharpness:
        status = BlurStatus.BLURRY
        message_key = GuidanceCategory.HOLD_STEADY
    else:
        status = BlurStatus.ACCEPTABLE
        message_key = GuidanceCategory.READY
    return QualityFinding(
        dimension=QualityDimension.BLUR,
        status=status,
        score=max(0.0, min(1.0, variance / max(thresholds.min_sharpness, 1))),
        message_key=message_key,
    )


def classify_contrast(
    image: NDArray[np.uint8],
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Classify contrast using grayscale standard deviation."""
    thresholds = thresholds or QualityThresholds()
    contrast = float(np.std(_to_gray(image)))
    if contrast < thresholds.min_contrast:
        status = ContrastStatus.LOW_CONTRAST
        message_key = GuidanceCategory.INCREASE_CONTRAST
    else:
        status = ContrastStatus.ACCEPTABLE
        message_key = GuidanceCategory.READY
    return QualityFinding(
        dimension=QualityDimension.CONTRAST,
        status=status,
        score=max(0.0, min(1.0, contrast / max(thresholds.min_contrast, 1))),
        message_key=message_key,
    )


def classify_basic_text_presence(
    image: NDArray[np.uint8],
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Estimate text presence without invoking OCR."""
    return estimate_text_presence_from_image(image, thresholds)


def assess_image_quality(
    image_input: ImageInput,
    thresholds: QualityThresholds | None = None,
) -> ImageQualityReport:
    """Assess one image and return an OCR-readiness decision."""
    thresholds = thresholds or QualityThresholds()
    image = image_input.decode()
    brightness = classify_brightness(image, thresholds)
    blur = classify_blur(image, thresholds)
    contrast = classify_contrast(image, thresholds)
    text_presence = classify_basic_text_presence(image, thresholds)

    issues: list[ImageProcessingErrorCode] = []
    if brightness.status == BrightnessStatus.TOO_DARK:
        issues.append(ImageProcessingErrorCode.IMAGE_TOO_DARK)
    elif brightness.status == BrightnessStatus.TOO_BRIGHT:
        issues.append(ImageProcessingErrorCode.IMAGE_TOO_BRIGHT)
    if blur.status == BlurStatus.BLURRY:
        issues.append(ImageProcessingErrorCode.IMAGE_TOO_BLURRY)
    if contrast.status == ContrastStatus.LOW_CONTRAST:
        issues.append(ImageProcessingErrorCode.IMAGE_LOW_CONTRAST)
    if text_presence.status == TextPresenceStatus.UNLIKELY_TEXT and not (
        blur.status == BlurStatus.BLURRY
        and contrast.status == ContrastStatus.ACCEPTABLE
    ) and not (
        contrast.status == ContrastStatus.LOW_CONTRAST
        and contrast.score > 0.1
    ):
        issues.append(ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND)
    elif text_presence.status == TextPresenceStatus.UNCERTAIN_TEXT:
        issues.append(ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN)

    quality_score = _overall_score(
        brightness.score,
        blur.score,
        contrast.score,
        text_presence.score,
    )
    if not issues and quality_score < thresholds.min_overall_score:
        issues.append(ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN)

    primary_issue = choose_primary_issue(issues)
    is_acceptable = primary_issue is None
    if is_acceptable:
        overall_status = OverallImageStatus.ACCEPTABLE
    elif primary_issue == ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN:
        overall_status = OverallImageStatus.UNCERTAIN
    else:
        overall_status = OverallImageStatus.REJECTED

    metadata = safe_image_metadata(
        source_id=image_input.source_id,
        image=image,
        metadata={
            "quality_score": quality_score,
            "brightness_status": brightness.status.value,
            "blur_status": blur.status.value,
            "contrast_status": contrast.status.value,
            "text_presence_status": text_presence.status.value,
            "guidance_category": guidance_for_issue(primary_issue).category.value,
        },
    )
    return ImageQualityReport(
        is_acceptable=is_acceptable,
        overall_status=overall_status,
        quality_score=quality_score,
        brightness_status=brightness.status,
        blur_status=blur.status,
        contrast_status=contrast.status,
        text_presence_status=text_presence.status,
        guidance=guidance_for_issue(primary_issue),
        primary_issue=primary_issue,
        metadata=metadata,
    )


def _to_gray(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _overall_score(*scores: float) -> float:
    if not scores:
        return 0.0
    return max(0.0, min(1.0, float(sum(scores)) / len(scores)))
