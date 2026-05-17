"""Image-processing model tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from modules.image_processing.image_models import (
    BrightnessStatus,
    BlurStatus,
    ContrastStatus,
    GuidanceCategory,
    GuidanceMessage,
    ImageInput,
    ImageProcessingErrorCode,
    ImageProcessingException,
    ImageQualityReport,
    OverallImageStatus,
    PreprocessingVariantName,
    PreprocessingVariantSet,
    QualityThresholds,
    TextPresenceStatus,
    VariantResult,
    image_log_metadata,
)


def _sample_image() -> np.ndarray:
    return np.full((24, 32, 3), 128, dtype=np.uint8)


def test_image_input_requires_exactly_one_source() -> None:
    image = _sample_image()

    request = ImageInput(image_array=image, source_id="sample")

    decoded = request.decode()
    assert decoded.shape == image.shape
    assert decoded is not image

    with pytest.raises(ValueError):
        ImageInput()

    with pytest.raises(ValueError):
        ImageInput(image_path="a.png", image_array=image)


def test_image_input_decodes_valid_bytes() -> None:
    image = _sample_image()
    ok, encoded = cv2.imencode(".png", image)
    assert ok

    decoded = ImageInput(image_bytes=encoded.tobytes()).decode()

    assert decoded.shape == image.shape


def test_image_input_reports_expected_decode_failures(tmp_path: Path) -> None:
    with pytest.raises(ImageProcessingException) as missing_path:
        ImageInput(image_path=tmp_path / "missing.png").decode()
    assert missing_path.value.error_code == ImageProcessingErrorCode.IMAGE_INPUT_UNREADABLE

    bad_path = tmp_path / "bad.txt"
    bad_path.write_text("not an image", encoding="utf-8")
    with pytest.raises(ImageProcessingException) as bad_file:
        ImageInput(image_path=bad_path).decode()
    assert bad_file.value.error_code == ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT

    with pytest.raises(ImageProcessingException) as empty_bytes:
        ImageInput(image_bytes=b"").decode()
    assert empty_bytes.value.error_code == ImageProcessingErrorCode.IMAGE_INPUT_MISSING

    with pytest.raises(ImageProcessingException) as invalid_bytes:
        ImageInput(image_bytes=b"not an image").decode()
    assert invalid_bytes.value.error_code == ImageProcessingErrorCode.IMAGE_UNSUPPORTED_FORMAT


def test_thresholds_validate_bounds() -> None:
    thresholds = QualityThresholds()
    assert thresholds.min_brightness < thresholds.max_brightness

    with pytest.raises(ValueError):
        QualityThresholds(min_brightness=200, max_brightness=100)

    with pytest.raises(ValueError):
        QualityThresholds(min_overall_score=1.5)


def test_guidance_report_and_variant_models_validate_contracts() -> None:
    guidance = GuidanceMessage(
        category=GuidanceCategory.READY,
        english_text="Ready.",
        arabic_text="جاهز.",
    )
    report = ImageQualityReport(
        is_acceptable=True,
        overall_status=OverallImageStatus.ACCEPTABLE,
        quality_score=0.95,
        brightness_status=BrightnessStatus.ACCEPTABLE,
        blur_status=BlurStatus.ACCEPTABLE,
        contrast_status=ContrastStatus.ACCEPTABLE,
        text_presence_status=TextPresenceStatus.LIKELY_TEXT,
        guidance=guidance,
    )

    assert report.is_acceptable is True

    with pytest.raises(ValueError):
        GuidanceMessage(
            category=GuidanceCategory.READY,
            english_text="Ready.",
            arabic_text="",
        )

    with pytest.raises(ValueError):
        ImageQualityReport(
            is_acceptable=False,
            overall_status=OverallImageStatus.REJECTED,
            quality_score=0.1,
            brightness_status=BrightnessStatus.TOO_DARK,
            blur_status=BlurStatus.ACCEPTABLE,
            contrast_status=ContrastStatus.ACCEPTABLE,
            text_presence_status=TextPresenceStatus.LIKELY_TEXT,
            guidance=guidance,
        )


def test_variant_set_requires_all_named_variants_and_preserves_original() -> None:
    image = _sample_image()
    variants = {
        name: VariantResult(name=name, image=image.copy())
        for name in PreprocessingVariantName
    }
    variant_set = PreprocessingVariantSet(
        source_id="sample",
        original_preserved=True,
        variants=variants,
    )

    assert set(variant_set.variants) == set(PreprocessingVariantName)

    with pytest.raises(ValueError):
        PreprocessingVariantSet(
            source_id="sample",
            original_preserved=True,
            variants={PreprocessingVariantName.ONLINE_LIGHT: variants[PreprocessingVariantName.ONLINE_LIGHT]},
        )


def test_image_log_metadata_excludes_image_and_text_content() -> None:
    report = ImageQualityReport(
        is_acceptable=False,
        overall_status=OverallImageStatus.REJECTED,
        quality_score=0.2,
        brightness_status=BrightnessStatus.TOO_DARK,
        blur_status=BlurStatus.ACCEPTABLE,
        contrast_status=ContrastStatus.ACCEPTABLE,
        text_presence_status=TextPresenceStatus.UNCERTAIN_TEXT,
        guidance=GuidanceMessage(
            category=GuidanceCategory.IMPROVE_LIGHTING,
            english_text="Improve lighting.",
            arabic_text="حسن الإضاءة.",
        ),
        primary_issue=ImageProcessingErrorCode.IMAGE_TOO_DARK,
        metadata={
            "image_bytes": b"secret",
            "raw_text": "private text",
            "debug_path": "debug_captures/private.png",
            "quality_source": "test",
        },
    )

    metadata = image_log_metadata(report)

    assert metadata["quality_source"] == "test"
    assert "secret" not in str(metadata)
    assert "private text" not in str(metadata)
    assert "debug_captures" not in str(metadata)
