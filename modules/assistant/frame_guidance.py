"""Camera-frame guidance for assisted OCR capture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrameGuidance:
    ready: bool
    message_en: str
    message_ar: str
    quality_summary: str


def guidance_from_capture(capture_result: Any) -> FrameGuidance:
    """Return human guidance from the latest capture/selection result."""
    selection = getattr(capture_result, "selection_result", None)
    candidate = None
    if selection is not None:
        candidate = getattr(selection, "selected_frame", None)
    if candidate is None and getattr(capture_result, "candidates", None):
        candidate = capture_result.candidates[0]
    report = getattr(candidate, "quality_report", None)
    if report is None:
        return FrameGuidance(
            ready=False,
            message_en="Point the camera toward printed text.",
            message_ar="وجه الكاميرا ناحية النص.",
            quality_summary="quality not available",
        )

    text_status = _value(getattr(report, "text_presence_status", None))
    blur_status = _value(getattr(report, "blur_status", None))
    brightness_status = _value(getattr(report, "brightness_status", None))
    contrast_status = _value(getattr(report, "contrast_status", None))
    score = float(getattr(report, "quality_score", 0.0))
    ready = bool(getattr(report, "is_acceptable", False)) or (
        score >= 0.50 and text_status in {"likely_text", "uncertain_text"}
    )

    if ready:
        return FrameGuidance(
            ready=True,
            message_en="Text is visible. Hold still.",
            message_ar="النص واضح. ثبت مكانك.",
            quality_summary=_summary(score, text_status, blur_status, brightness_status),
        )
    if brightness_status in {"too_dark", "too_bright"}:
        return FrameGuidance(
            ready=False,
            message_en="Adjust the light, then hold the text steady.",
            message_ar="ظبط الإضاءة وثبت النص.",
            quality_summary=_summary(score, text_status, blur_status, brightness_status),
        )
    if blur_status != "acceptable":
        return FrameGuidance(
            ready=False,
            message_en="Hold the paper steady and move it a little closer.",
            message_ar="ثبت الورقة وقربها شوية.",
            quality_summary=_summary(score, text_status, blur_status, brightness_status),
        )
    if text_status not in {"likely_text", "uncertain_text"}:
        return FrameGuidance(
            ready=False,
            message_en="Move the text into the center of the camera.",
            message_ar="حرك النص لمنتصف الكاميرا.",
            quality_summary=_summary(score, text_status, blur_status, brightness_status),
        )
    if contrast_status != "acceptable":
        return FrameGuidance(
            ready=False,
            message_en="Use a clearer background behind the text.",
            message_ar="خلي خلفية النص أوضح.",
            quality_summary=_summary(score, text_status, blur_status, brightness_status),
        )
    return FrameGuidance(
        ready=False,
        message_en="Hold still while I find the clearest frame.",
        message_ar="ثبت مكانك لحد ما ألاقي أوضح صورة.",
        quality_summary=_summary(score, text_status, blur_status, brightness_status),
    )


def _value(value: Any) -> str:
    return str(getattr(value, "value", value) or "unknown")


def _summary(score: float, text_status: str, blur_status: str, brightness_status: str) -> str:
    return (
        f"score {score:.2f}, text {text_status}, "
        f"blur {blur_status}, light {brightness_status}"
    )


__all__ = ["FrameGuidance", "guidance_from_capture"]
