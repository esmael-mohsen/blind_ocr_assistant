"""Image preprocessing tests."""

from __future__ import annotations

import cv2
import numpy as np

from modules.image_processing.image_models import (
    GuidanceCategory,
    ImageInput,
    ImageProcessingErrorCode,
    OverallImageStatus,
    PreprocessingVariantName,
)
from modules.image_processing.preprocessing import (
    create_preprocessing_variants,
    create_variants_after_quality_check,
)
from modules.image_processing.quality_checker import assess_image_quality, get_guidance


def _text_image() -> np.ndarray:
    image = np.full((120, 180, 3), 240, dtype=np.uint8)
    cv2.rectangle(image, (20, 24), (156, 40), (20, 20, 20), -1)
    cv2.rectangle(image, (20, 58), (138, 74), (20, 20, 20), -1)
    cv2.rectangle(image, (20, 92), (160, 108), (20, 20, 20), -1)
    return image


def _low_contrast_image() -> np.ndarray:
    image = np.full((120, 180, 3), 126, dtype=np.uint8)
    cv2.rectangle(image, (20, 32), (150, 48), (145, 145, 145), -1)
    cv2.rectangle(image, (20, 72), (136, 88), (145, 145, 145), -1)
    return image


def _contrast(image: np.ndarray) -> float:
    return float(np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)))


def test_preprocessing_returns_required_variant_names() -> None:
    variants = create_preprocessing_variants(
        ImageInput(image_array=_text_image(), source_id="accepted")
    )

    assert set(variants.variants) == set(PreprocessingVariantName)
    assert all(result.success for result in variants.variants.values())
    assert variants.metadata["variant_names"] == [
        PreprocessingVariantName.ONLINE_LIGHT.value,
        PreprocessingVariantName.LOCAL_NATURAL.value,
        PreprocessingVariantName.EMERGENCY_STRONG.value,
    ]


def test_preprocessing_preserves_original_image() -> None:
    image = _text_image()
    before = image.copy()

    variants = create_preprocessing_variants(ImageInput(image_array=image))

    assert np.array_equal(image, before)
    assert variants.original_preserved is True


def test_preprocessing_improves_low_contrast_variant_without_exact_thresholds() -> None:
    image = _low_contrast_image()

    variants = create_preprocessing_variants(ImageInput(image_array=image))

    emergency = variants.variants[PreprocessingVariantName.EMERGENCY_STRONG]
    assert emergency.image is not None
    assert _contrast(emergency.image) > _contrast(image)


def test_preprocessing_reports_per_variant_failure(monkeypatch) -> None:
    def fail_variant(_image: np.ndarray) -> np.ndarray:
        raise RuntimeError("variant failed")

    monkeypatch.setattr(
        "modules.image_processing.preprocessing._build_online_light",
        fail_variant,
    )

    variants = create_preprocessing_variants(ImageInput(image_array=_text_image()))
    failed = variants.variants[PreprocessingVariantName.ONLINE_LIGHT]

    assert failed.success is False
    assert failed.error_code == ImageProcessingErrorCode.IMAGE_PREPROCESSING_FAILED
    assert variants.variants[PreprocessingVariantName.LOCAL_NATURAL].success is True


def test_rejected_images_do_not_enter_preprocessing_in_normal_workflow() -> None:
    image = np.full((120, 180, 3), 20, dtype=np.uint8)
    image_input = ImageInput(image_array=image)
    report = assess_image_quality(image_input)

    result = create_variants_after_quality_check(image_input, report)

    assert result is report
    assert result.is_acceptable is False
    assert result.overall_status != OverallImageStatus.ACCEPTABLE
    assert result.guidance.category == GuidanceCategory.IMPROVE_LIGHTING
    assert get_guidance(GuidanceCategory.IMPROVE_LIGHTING).english_text
