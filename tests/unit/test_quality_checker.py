"""Image quality checker tests."""

from __future__ import annotations

import cv2
import numpy as np

from modules.image_processing.image_models import (
    BrightnessStatus,
    BlurStatus,
    ContrastStatus,
    GuidanceCategory,
    ImageInput,
    ImageProcessingErrorCode,
    OverallImageStatus,
    QualityThresholds,
    TextPresenceStatus,
)
from modules.image_processing.quality_checker import (
    assess_image_quality,
    classify_blur,
    classify_brightness,
    classify_contrast,
    choose_primary_issue,
    get_guidance,
    guidance_for_issue,
)


def make_text_image(kind: str = "english") -> np.ndarray:
    image = np.full((160, 260, 3), 245, dtype=np.uint8)
    cv2.rectangle(image, (24, 30), (236, 48), (20, 20, 20), -1)
    cv2.rectangle(image, (24, 68), (210, 86), (20, 20, 20), -1)
    cv2.rectangle(image, (24, 106), (224, 124), (20, 20, 20), -1)
    if kind == "arabic":
        cv2.rectangle(image, (60, 32), (236, 48), (20, 20, 20), -1)
        cv2.rectangle(image, (86, 70), (236, 86), (20, 20, 20), -1)
    elif kind == "mixed":
        cv2.rectangle(image, (24, 136), (138, 150), (20, 20, 20), -1)
        cv2.rectangle(image, (150, 136), (236, 150), (20, 20, 20), -1)
    return image


def make_dark_image() -> np.ndarray:
    return np.full((120, 180, 3), 20, dtype=np.uint8)


def make_bright_image() -> np.ndarray:
    return np.full((120, 180, 3), 250, dtype=np.uint8)


def make_blurry_image() -> np.ndarray:
    return cv2.GaussianBlur(make_text_image(), (51, 51), 0)


def make_low_contrast_image() -> np.ndarray:
    image = np.full((120, 180, 3), 125, dtype=np.uint8)
    cv2.rectangle(image, (24, 36), (150, 50), (145, 145, 145), -1)
    cv2.rectangle(image, (24, 70), (130, 84), (145, 145, 145), -1)
    return image


def make_no_text_image() -> np.ndarray:
    return np.full((120, 180, 3), 220, dtype=np.uint8)


def make_borderline_image() -> np.ndarray:
    image = np.full((140, 220, 3), 235, dtype=np.uint8)
    cv2.rectangle(image, (70, 60), (150, 67), (80, 80, 80), -1)
    return image


def test_guidance_catalog_contains_bilingual_messages() -> None:
    for category in GuidanceCategory:
        guidance = get_guidance(category)

        assert guidance.category == category
        assert guidance.english_text.strip()
        assert guidance.arabic_text.strip()


def test_guidance_for_issue_maps_expected_categories() -> None:
    assert (
        guidance_for_issue(ImageProcessingErrorCode.IMAGE_TOO_DARK).category
        == GuidanceCategory.IMPROVE_LIGHTING
    )
    assert (
        guidance_for_issue(ImageProcessingErrorCode.IMAGE_TOO_BLURRY).category
        == GuidanceCategory.HOLD_STEADY
    )
    assert (
        guidance_for_issue(ImageProcessingErrorCode.IMAGE_LOW_CONTRAST).category
        == GuidanceCategory.INCREASE_CONTRAST
    )
    assert (
        guidance_for_issue(ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND).category
        == GuidanceCategory.POINT_TO_TEXT
    )
    assert (
        guidance_for_issue(ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN).category
        == GuidanceCategory.RECAPTURE
    )
    assert guidance_for_issue(None).category == GuidanceCategory.READY


def test_primary_issue_uses_stable_actionable_priority() -> None:
    issue = choose_primary_issue(
        [
            ImageProcessingErrorCode.IMAGE_LOW_CONTRAST,
            ImageProcessingErrorCode.IMAGE_TOO_BLURRY,
            ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND,
        ]
    )

    assert issue == ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND


def test_brightness_classifies_dark_bright_and_acceptable_images() -> None:
    thresholds = QualityThresholds()

    assert classify_brightness(make_dark_image(), thresholds).status == BrightnessStatus.TOO_DARK
    assert classify_brightness(make_bright_image(), thresholds).status == BrightnessStatus.TOO_BRIGHT
    assert (
        classify_brightness(make_text_image(), thresholds).status
        == BrightnessStatus.ACCEPTABLE
    )


def test_blur_classifies_blurry_and_acceptable_images() -> None:
    thresholds = QualityThresholds()

    assert classify_blur(make_blurry_image(), thresholds).status == BlurStatus.BLURRY
    assert classify_blur(make_text_image(), thresholds).status == BlurStatus.ACCEPTABLE


def test_contrast_classifies_low_contrast_and_acceptable_images() -> None:
    thresholds = QualityThresholds()

    assert (
        classify_contrast(make_low_contrast_image(), thresholds).status
        == ContrastStatus.LOW_CONTRAST
    )
    assert classify_contrast(make_text_image(), thresholds).status == ContrastStatus.ACCEPTABLE


def test_overall_quality_decision_rejects_poor_images() -> None:
    cases = [
        (make_dark_image(), ImageProcessingErrorCode.IMAGE_TOO_DARK),
        (make_bright_image(), ImageProcessingErrorCode.IMAGE_TOO_BRIGHT),
        (make_blurry_image(), ImageProcessingErrorCode.IMAGE_TOO_BLURRY),
        (make_low_contrast_image(), ImageProcessingErrorCode.IMAGE_LOW_CONTRAST),
        (make_no_text_image(), ImageProcessingErrorCode.IMAGE_TEXT_NOT_FOUND),
    ]

    for image, expected_issue in cases:
        report = assess_image_quality(ImageInput(image_array=image, source_id="case"))

        assert report.is_acceptable is False
        assert report.primary_issue == expected_issue
        assert report.guidance.english_text
        assert report.guidance.arabic_text


def test_borderline_and_uncertain_quality_are_blocked() -> None:
    report = assess_image_quality(ImageInput(image_array=make_borderline_image()))

    assert report.is_acceptable is False
    assert report.overall_status == OverallImageStatus.UNCERTAIN
    assert report.primary_issue == ImageProcessingErrorCode.IMAGE_QUALITY_UNCERTAIN
    assert report.guidance.category == GuidanceCategory.RECAPTURE


def test_multiple_quality_problems_use_priority_guidance() -> None:
    image = make_dark_image()
    report = assess_image_quality(ImageInput(image_array=image))

    assert report.primary_issue == ImageProcessingErrorCode.IMAGE_TOO_DARK
    assert report.guidance.category == GuidanceCategory.IMPROVE_LIGHTING


def test_acceptable_arabic_english_and_mixed_images_pass_quality_gate() -> None:
    for kind in ("arabic", "english", "mixed"):
        report = assess_image_quality(ImageInput(image_array=make_text_image(kind)))

        assert report.is_acceptable is True
        assert report.overall_status == OverallImageStatus.ACCEPTABLE
        assert report.text_presence_status == TextPresenceStatus.LIKELY_TEXT
        assert report.guidance.category == GuidanceCategory.READY
        assert report.quality_score >= QualityThresholds().min_overall_score
