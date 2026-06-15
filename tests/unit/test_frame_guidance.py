"""Tests for guided capture frame guidance."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.frame_guidance import guidance_from_capture


def _capture(report):
    candidate = SimpleNamespace(quality_report=report)
    return SimpleNamespace(selection_result=SimpleNamespace(selected_frame=candidate), candidates=[candidate])


def test_frame_guidance_ready_when_text_is_visible() -> None:
    guidance = guidance_from_capture(
        _capture(
            SimpleNamespace(
                is_acceptable=True,
                quality_score=0.8,
                text_presence_status=SimpleNamespace(value="likely_text"),
                blur_status=SimpleNamespace(value="acceptable"),
                brightness_status=SimpleNamespace(value="acceptable"),
                contrast_status=SimpleNamespace(value="acceptable"),
            )
        )
    )

    assert guidance.ready is True
    assert "Hold still" in guidance.message_en


def test_frame_guidance_reports_poor_light() -> None:
    guidance = guidance_from_capture(
        _capture(
            SimpleNamespace(
                is_acceptable=False,
                quality_score=0.2,
                text_presence_status=SimpleNamespace(value="unlikely_text"),
                blur_status=SimpleNamespace(value="acceptable"),
                brightness_status=SimpleNamespace(value="too_dark"),
                contrast_status=SimpleNamespace(value="acceptable"),
            )
        )
    )

    assert guidance.ready is False
    assert "light" in guidance.message_en.lower()
