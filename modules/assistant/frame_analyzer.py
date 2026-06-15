"""Cheap frame analysis used to gate OCR capture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.assistant.runtime_state import FrameReadiness


@dataclass
class FrameAnalyzer:
    """Convert image-quality reports into stable read/capture readiness."""

    stable_required_frames: int = 3
    text_confidence_threshold: float = 0.55
    _stable_frames: int = 0
    _last_guidance_code: str = ""

    def analyze_capture(self, capture_result: Any) -> FrameReadiness:
        """Analyze the latest preview capture without invoking OCR."""
        report = _best_quality_report(capture_result)
        if report is None:
            self._stable_frames = 0
            return FrameReadiness(
                guidance_code="warming_up",
                guidance="Camera is warming up. Point it toward printed text.",
                quality_summary="quality not available",
            )

        text_status = _value(getattr(report, "text_presence_status", None))
        blur_status = _value(getattr(report, "blur_status", None))
        brightness_status = _value(getattr(report, "brightness_status", None))
        contrast_status = _value(getattr(report, "contrast_status", None))
        score = float(getattr(report, "quality_score", 0.0) or 0.0)
        text_confidence = _text_confidence(
            text_status,
            score,
            threshold=self.text_confidence_threshold,
        )
        brightness_ok = brightness_status == "acceptable"
        blur_ok = blur_status == "acceptable"
        contrast_ok = contrast_status == "acceptable"
        inferred_text = (
            text_confidence < self.text_confidence_threshold
            and text_status == "unlikely_text"
            and score >= 0.60
            and brightness_ok
            and blur_ok
        )
        has_text = text_confidence >= self.text_confidence_threshold or inferred_text
        position = _position_analysis(capture_result)
        centered = position["position_hint"] == "centered"
        if has_text and centered:
            self._stable_frames += 1
        else:
            self._stable_frames = 0
        strict_quality_ready = bool(getattr(report, "is_acceptable", False))
        gate_text_status = "inferred_text" if inferred_text else text_status
        relaxed_quality_ready = _relaxed_quality_ready(
            score=score,
            text_status=gate_text_status,
            brightness_status=brightness_status,
            blur_status=blur_status,
            contrast_status=contrast_status,
        )
        ready = (
            has_text
            and centered
            and self._stable_frames >= max(1, self.stable_required_frames)
            and (strict_quality_ready or relaxed_quality_ready)
        )
        guidance_code, guidance = _guidance(
            ready=ready,
            relaxed=ready and not strict_quality_ready,
            has_text=has_text,
            inferred_text=inferred_text,
            brightness_status=brightness_status,
            blur_status=blur_status,
            contrast_ok=contrast_ok,
            stable_frames=self._stable_frames,
            stable_required_frames=max(1, self.stable_required_frames),
            position_hint=position["position_hint"] if has_text else "unknown",
        )
        return FrameReadiness(
            has_text=has_text,
            text_confidence=text_confidence,
            stable_frames=self._stable_frames,
            centered=centered,
            position_hint=position["position_hint"] if has_text else "unknown",
            horizontal_offset=position["horizontal_offset"] if has_text else 0.0,
            vertical_offset=position["vertical_offset"] if has_text else 0.0,
            size_hint=position["size_hint"] if has_text else "unknown",
            brightness_ok=brightness_ok,
            blur_ok=blur_ok,
            ready_to_capture=ready,
            guidance_code=guidance_code,
            guidance=guidance,
            quality_summary=(
                f"score {score:.2f}, text {text_status}, blur {blur_status}, "
                f"light {brightness_status}, confidence {text_confidence:.2f}, "
                f"inferred {inferred_text}, stable {self._stable_frames}"
            ),
        )


def _best_quality_report(capture_result: Any) -> Any | None:
    selection = getattr(capture_result, "selection_result", None)
    selected = getattr(selection, "selected_frame", None) if selection is not None else None
    if selected is not None and getattr(selected, "quality_report", None) is not None:
        return selected.quality_report
    reports = [
        getattr(candidate, "quality_report", None)
        for candidate in getattr(capture_result, "candidates", []) or []
        if getattr(candidate, "quality_report", None) is not None
    ]
    if not reports:
        return None
    return max(reports, key=lambda item: float(getattr(item, "quality_score", 0.0) or 0.0))


def _best_frame_image(capture_result: Any) -> Any | None:
    selection = getattr(capture_result, "selection_result", None)
    selected = getattr(selection, "selected_frame", None) if selection is not None else None
    image = getattr(selected, "rgb_image", None) if selected is not None else None
    if image is not None:
        return image
    for candidate in getattr(capture_result, "candidates", []) or []:
        image = getattr(candidate, "rgb_image", None)
        if image is not None:
            return image
    return None


def _position_analysis(capture_result: Any) -> dict[str, Any]:
    image = _best_frame_image(capture_result)
    shape = getattr(image, "shape", None)
    if image is None or not shape or len(shape) < 2:
        return {
            "position_hint": "centered",
            "horizontal_offset": 0.0,
            "vertical_offset": 0.0,
            "size_hint": "unknown",
        }
    import numpy as np

    height, width = int(shape[0]), int(shape[1])
    if height <= 0 or width <= 0:
        return {
            "position_hint": "centered",
            "horizontal_offset": 0.0,
            "vertical_offset": 0.0,
            "size_hint": "unknown",
        }
    gray = image.mean(axis=2) if getattr(image, "ndim", 0) == 3 else image
    threshold = min(220.0, float(np.percentile(gray, 35)))
    mask = gray <= threshold
    mask = _remove_border_touching_components(mask)
    ys, xs = np.where(mask)
    if xs.size < max(10, int(width * height * 0.002)):
        return {
            "position_hint": "centered",
            "horizontal_offset": 0.0,
            "vertical_offset": 0.0,
            "size_hint": "unknown",
        }
    x1, x2 = int(xs.min()), int(xs.max())
    y1, y2 = int(ys.min()), int(ys.max())
    center_x = ((x1 + x2) / 2.0) / max(1, width)
    center_y = ((y1 + y2) / 2.0) / max(1, height)
    horizontal_offset = center_x - 0.5
    vertical_offset = center_y - 0.5
    position_hint = "centered"
    if horizontal_offset < -0.18:
        position_hint = "move_right"
    elif horizontal_offset > 0.18:
        position_hint = "move_left"
    elif vertical_offset < -0.18:
        position_hint = "move_down"
    elif vertical_offset > 0.18:
        position_hint = "move_up"
    size_hint = "ok"
    return {
        "position_hint": position_hint,
        "horizontal_offset": horizontal_offset,
        "vertical_offset": vertical_offset,
        "size_hint": size_hint,
    }


def _remove_border_touching_components(mask: Any) -> Any:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return mask
    binary = mask.astype("uint8")
    count, labels, stats, _centroids = cv2.connectedComponentsWithStats(binary, 8)
    if count <= 1:
        return mask
    cleaned = np.zeros_like(binary, dtype=bool)
    height, width = binary.shape[:2]
    min_area = max(4, int(height * width * 0.0002))
    for label in range(1, count):
        x, y, w, h, area = stats[label]
        touches_border = x <= 0 or y <= 0 or x + w >= width or y + h >= height
        if touches_border or area < min_area:
            continue
        cleaned[labels == label] = True
    return cleaned


def _text_confidence(text_status: str, score: float, *, threshold: float) -> float:
    if text_status == "likely_text":
        return max(0.80, min(1.0, score))
    if text_status == "uncertain_text":
        # The cheap detector is intentionally conservative; uncertain_text still
        # means "there is probably text, but quality may need guidance".
        return max(threshold, min(0.74, threshold + max(0.0, score) * 0.5))
    return min(0.20, max(0.0, score * 0.25))


def _relaxed_quality_ready(
    *,
    score: float,
    text_status: str,
    brightness_status: str,
    blur_status: str,
    contrast_status: str,
) -> bool:
    """Allow practical capture when text is visible but quality labels are imperfect."""
    if text_status not in {"likely_text", "uncertain_text", "inferred_text"}:
        return False
    if brightness_status in {"too_dark", "too_bright"} and score < 0.48:
        return False
    if blur_status != "acceptable" and score < 0.52:
        return False
    if contrast_status != "acceptable" and score < 0.38:
        return False
    return score >= 0.38


def _guidance(
    *,
    ready: bool,
    relaxed: bool,
    has_text: bool,
    inferred_text: bool,
    brightness_status: str,
    blur_status: str,
    contrast_ok: bool,
    stable_frames: int,
    stable_required_frames: int,
    position_hint: str,
) -> tuple[str, str]:
    if has_text and position_hint != "centered":
        return position_hint, _position_guidance(position_hint)
    if ready:
        if inferred_text:
            return "ready_low_quality", "Text is visible enough. Capturing the best frame now."
        if relaxed:
            return "ready_low_quality", "Text is visible. Capturing the best frame now."
        return "ready", "Text is clear. Capturing now."
    if not has_text:
        return "no_text", "Move printed text into the camera view."
    if brightness_status == "too_dark":
        return "too_dark", "Lighting is low. Move closer to light."
    if brightness_status == "too_bright":
        return "too_bright", "There is too much glare. Tilt the paper slightly."
    if blur_status != "acceptable":
        return "blurry", "Hold the paper and camera steady."
    if not contrast_ok:
        return "low_contrast", "Use a clearer background behind the text."
    if stable_frames < stable_required_frames:
        return "hold_still", "Text is visible. Hold still."
    return "adjust", "Adjust the text position slightly."


def _position_guidance(position_hint: str) -> str:
    if position_hint == "move_right":
        return "حرك الورقة يمين شوية."
    if position_hint == "move_left":
        return "حرك الورقة شمال شوية."
    if position_hint == "move_down":
        return "نزل الورقة شوية."
    if position_hint == "move_up":
        return "ارفع الورقة شوية."
    if position_hint == "move_closer":
        return "قرب الورقة شوية."
    if position_hint == "move_farther":
        return "بعد الورقة شوية."
    return "حط النص في نص الكاميرا."


def _value(value: Any) -> str:
    return str(getattr(value, "value", value) or "unknown")


__all__ = ["FrameAnalyzer"]
