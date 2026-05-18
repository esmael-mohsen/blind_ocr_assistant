"""OCR-oriented preprocessing variants for accepted still images."""

from __future__ import annotations

from collections.abc import Callable

import cv2
import numpy as np
from numpy.typing import NDArray

from modules.image_processing.image_models import (
    ImageInput,
    ImageProcessingErrorCode,
    ImageQualityReport,
    PreprocessingVariantName,
    PreprocessingVariantSet,
    VariantResult,
    safe_image_metadata,
)


VariantBuilder = Callable[[NDArray[np.uint8]], NDArray[np.uint8]]


def create_preprocessing_variants(image_input: ImageInput) -> PreprocessingVariantSet:
    """Create named OCR-preparation variants while preserving the original."""
    original = image_input.decode()
    source = original.copy()
    builders: dict[PreprocessingVariantName, VariantBuilder] = {
        PreprocessingVariantName.ONLINE_LIGHT: _build_online_light,
        PreprocessingVariantName.LOCAL_NATURAL: _build_local_natural,
        PreprocessingVariantName.EMERGENCY_STRONG: _build_emergency_strong,
    }
    variants: dict[PreprocessingVariantName, VariantResult] = {}
    for name, builder in builders.items():
        try:
            variants[name] = VariantResult(name=name, image=builder(source.copy()))
        except Exception as exc:  # noqa: BLE001 - convert variant failures to results.
            variants[name] = VariantResult(
                name=name,
                success=False,
                error_code=ImageProcessingErrorCode.IMAGE_PREPROCESSING_FAILED,
                error_message=str(exc) or f"{name.value} preprocessing failed",
            )
    metadata = safe_image_metadata(
        source_id=image_input.source_id,
        image=original,
        metadata={
            "variant_names": [name.value for name in variants],
            "failed_variants": [
                name.value for name, result in variants.items() if not result.success
            ],
        },
    )
    return PreprocessingVariantSet(
        source_id=image_input.source_id,
        original_preserved=bool(np.array_equal(original, source)),
        variants=variants,
        metadata=metadata,
    )


def create_variants_after_quality_check(
    image_input: ImageInput,
    report: ImageQualityReport,
) -> PreprocessingVariantSet | ImageQualityReport:
    """Normal workflow guard: preprocess only accepted images."""
    if not report.is_acceptable:
        return report
    return create_preprocessing_variants(image_input)


def _build_online_light(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))
    enhanced = clahe.apply(lightness)
    return cv2.cvtColor(cv2.merge((enhanced, a_channel, b_channel)), cv2.COLOR_LAB2BGR)


def _build_local_natural(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    return cv2.convertScaleAbs(image, alpha=1.05, beta=2)


def _build_emergency_strong(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    normalized = cv2.normalize(blurred, None, 0, 255, cv2.NORM_MINMAX)
    _, thresholded = cv2.threshold(
        normalized,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    if float(np.std(thresholded)) < float(np.std(gray)):
        thresholded = normalized
    sharpened = cv2.addWeighted(thresholded, 1.4, normalized, -0.4, 0)
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
