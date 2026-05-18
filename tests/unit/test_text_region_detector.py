"""Text-region detector tests."""

from __future__ import annotations

import sys

import cv2
import numpy as np

from modules.image_processing.image_models import ImageInput, TextPresenceStatus
from modules.image_processing.text_region_detector import estimate_text_presence


def _text_like(kind: str = "english") -> np.ndarray:
    image = np.full((150, 240, 3), 245, dtype=np.uint8)
    cv2.rectangle(image, (24, 28), (210, 44), (20, 20, 20), -1)
    cv2.rectangle(image, (24, 66), (190, 82), (20, 20, 20), -1)
    cv2.rectangle(image, (24, 104), (220, 120), (20, 20, 20), -1)
    if kind == "arabic":
        cv2.rectangle(image, (70, 30), (220, 46), (20, 20, 20), -1)
    elif kind == "mixed":
        cv2.rectangle(image, (24, 130), (110, 142), (20, 20, 20), -1)
        cv2.rectangle(image, (130, 130), (218, 142), (20, 20, 20), -1)
    return image


def _decorative() -> np.ndarray:
    image = np.full((150, 240, 3), 230, dtype=np.uint8)
    for x in range(30, 220, 40):
        cv2.circle(image, (x, 75), 14, (30, 30, 30), 2)
    return image


def _uncertain() -> np.ndarray:
    image = np.full((150, 240, 3), 238, dtype=np.uint8)
    cv2.rectangle(image, (82, 70), (158, 77), (30, 30, 30), -1)
    return image


def test_likely_text_estimation_for_arabic_english_and_mixed_inputs() -> None:
    for kind in ("arabic", "english", "mixed"):
        finding = estimate_text_presence(ImageInput(image_array=_text_like(kind)))

        assert finding.status == TextPresenceStatus.LIKELY_TEXT
        assert finding.score > 0


def test_unlikely_text_estimation_for_blank_and_decorative_inputs() -> None:
    blank = np.full((150, 240, 3), 240, dtype=np.uint8)

    assert (
        estimate_text_presence(ImageInput(image_array=blank)).status
        == TextPresenceStatus.UNLIKELY_TEXT
    )
    assert (
        estimate_text_presence(ImageInput(image_array=_decorative())).status
        == TextPresenceStatus.UNLIKELY_TEXT
    )


def test_uncertain_text_estimation_for_sparse_partial_or_edge_text() -> None:
    finding = estimate_text_presence(ImageInput(image_array=_uncertain()))

    assert finding.status == TextPresenceStatus.UNCERTAIN_TEXT


def test_text_presence_estimation_is_deterministic() -> None:
    image_input = ImageInput(image_array=_text_like())

    first = estimate_text_presence(image_input)
    second = estimate_text_presence(image_input)

    assert first.status == second.status
    assert first.score == second.score


def test_text_presence_estimation_does_not_invoke_ocr_modules(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "modules.ocr", None)

    finding = estimate_text_presence(ImageInput(image_array=_text_like()))

    assert finding.status == TextPresenceStatus.LIKELY_TEXT
