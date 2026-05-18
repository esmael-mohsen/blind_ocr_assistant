"""Deterministic text-presence estimation without OCR."""

from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray

from modules.image_processing.image_models import (
    GuidanceCategory,
    ImageInput,
    QualityDimension,
    QualityFinding,
    QualityThresholds,
    TextPresenceStatus,
)


def estimate_text_presence(
    image_input: ImageInput,
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Estimate whether a still image probably contains text without OCR."""
    image = image_input.decode()
    return estimate_text_presence_from_image(image, thresholds)


def estimate_text_presence_from_image(
    image: NDArray[np.uint8],
    thresholds: QualityThresholds | None = None,
) -> QualityFinding:
    """Estimate text presence from a decoded image array."""
    thresholds = thresholds or QualityThresholds()
    gray = _to_gray(image)
    binary = _foreground_mask(gray)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = float(gray.shape[0] * gray.shape[1])
    text_like_area = 0.0
    text_like_count = 0

    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if width < 8 or height < 3:
            continue
        aspect = width / max(height, 1)
        relative_height = height / max(gray.shape[0], 1)
        area = width * height
        extent = cv2.contourArea(contour) / max(area, 1)
        if 2.0 <= aspect <= 35.0 and relative_height <= 0.28 and extent >= 0.45:
            text_like_area += area
            text_like_count += 1

    edge_density = float(np.count_nonzero(cv2.Canny(gray, 80, 160))) / image_area
    score = min(1.0, (text_like_area / image_area) * 4.0 + edge_density * 0.6)

    if text_like_count == 0:
        score = min(score, edge_density * 0.25)
    elif text_like_count == 1:
        score *= 0.85

    if score >= thresholds.min_text_presence:
        status = TextPresenceStatus.LIKELY_TEXT
        message_key = GuidanceCategory.READY
    elif score >= thresholds.min_text_presence / 3.0:
        status = TextPresenceStatus.UNCERTAIN_TEXT
        message_key = GuidanceCategory.RECAPTURE
    else:
        status = TextPresenceStatus.UNLIKELY_TEXT
        message_key = GuidanceCategory.POINT_TO_TEXT

    return QualityFinding(
        dimension=QualityDimension.TEXT_PRESENCE,
        status=status,
        score=score,
        message_key=message_key,
    )


def _to_gray(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _foreground_mask(gray: NDArray[np.uint8]) -> NDArray[np.uint8]:
    median = float(np.median(gray))
    _, dark = cv2.threshold(gray, max(0, median - 20), 255, cv2.THRESH_BINARY_INV)
    _, light = cv2.threshold(gray, min(255, median + 20), 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_or(dark, light)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 2))
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
