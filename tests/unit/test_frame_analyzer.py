"""Tests for frame readiness analysis."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from modules.assistant.frame_analyzer import FrameAnalyzer


def _capture(
    *,
    text="likely_text",
    blur="acceptable",
    light="acceptable",
    contrast="acceptable",
    score=0.8,
    image=None,
):
    report = SimpleNamespace(
        text_presence_status=SimpleNamespace(value=text),
        blur_status=SimpleNamespace(value=blur),
        brightness_status=SimpleNamespace(value=light),
        contrast_status=SimpleNamespace(value=contrast),
        quality_score=score,
    )
    candidate = SimpleNamespace(quality_report=report, rgb_image=image)
    return SimpleNamespace(selection_result=SimpleNamespace(selected_frame=candidate), candidates=[candidate])


def _document_image(*, x1=70, y1=50, x2=130, y2=110):
    image = np.full((160, 200, 3), 245, dtype=np.uint8)
    image[y1:y2, x1:x2] = 20
    return image


def _paper_on_dark_table_with_center_text():
    image = np.full((160, 200, 3), 35, dtype=np.uint8)
    image[30:130, 40:160] = 245
    image[72:78, 82:118] = 20
    image[86:92, 78:122] = 20
    return image


def test_readiness_requires_stable_text_frames():
    analyzer = FrameAnalyzer(stable_required_frames=3, text_confidence_threshold=0.55)

    first = analyzer.analyze_capture(_capture())
    second = analyzer.analyze_capture(_capture())
    third = analyzer.analyze_capture(_capture())

    assert first.ready_to_capture is False
    assert second.ready_to_capture is False
    assert third.ready_to_capture is True
    assert third.stable_frames == 3


def test_readiness_resets_when_text_disappears():
    analyzer = FrameAnalyzer(stable_required_frames=2, text_confidence_threshold=0.55)

    analyzer.analyze_capture(_capture())
    missing = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.2))

    assert missing.has_text is False
    assert missing.stable_frames == 0
    assert missing.ready_to_capture is False


def test_visible_text_stability_is_not_reset_by_imperfect_contrast():
    analyzer = FrameAnalyzer(stable_required_frames=3, text_confidence_threshold=0.55)

    first = analyzer.analyze_capture(_capture(contrast="low_contrast", score=0.42))
    second = analyzer.analyze_capture(_capture(contrast="low_contrast", score=0.42))
    third = analyzer.analyze_capture(_capture(contrast="low_contrast", score=0.42))

    assert first.has_text is True
    assert second.stable_frames == 2
    assert third.ready_to_capture is True
    assert third.guidance_code == "ready_low_quality"


def test_high_quality_unlikely_text_is_treated_as_inferred_visible_text():
    analyzer = FrameAnalyzer(stable_required_frames=3, text_confidence_threshold=0.55)

    first = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.65))
    second = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.65))
    third = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.65))

    assert first.has_text is True
    assert second.stable_frames == 2
    assert third.ready_to_capture is True
    assert third.guidance_code == "ready_low_quality"
    assert "inferred True" in third.quality_summary


def test_low_quality_unlikely_text_still_does_not_capture():
    analyzer = FrameAnalyzer(stable_required_frames=2, text_confidence_threshold=0.55)

    first = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.35))
    second = analyzer.analyze_capture(_capture(text="unlikely_text", score=0.35))

    assert first.has_text is False
    assert second.ready_to_capture is False


def test_uncertain_text_counts_as_visible_but_waits_for_stability():
    analyzer = FrameAnalyzer(stable_required_frames=2, text_confidence_threshold=0.55)

    first = analyzer.analyze_capture(_capture(text="uncertain_text", score=0.42))
    second = analyzer.analyze_capture(_capture(text="uncertain_text", score=0.42))

    assert first.has_text is True
    assert first.ready_to_capture is False
    assert second.ready_to_capture is True


def test_position_guidance_moves_left_text_right_before_capture():
    analyzer = FrameAnalyzer(stable_required_frames=1, text_confidence_threshold=0.55)

    result = analyzer.analyze_capture(_capture(image=_document_image(x1=5, x2=55)))

    assert result.ready_to_capture is False
    assert result.centered is False
    assert result.position_hint == "move_right"
    assert result.guidance_code == "move_right"
    assert "يمين" in result.guidance


def test_position_guidance_moves_right_text_left_before_capture():
    analyzer = FrameAnalyzer(stable_required_frames=1, text_confidence_threshold=0.55)

    result = analyzer.analyze_capture(_capture(image=_document_image(x1=145, x2=195)))

    assert result.ready_to_capture is False
    assert result.position_hint == "move_left"
    assert result.guidance_code == "move_left"
    assert "شمال" in result.guidance


def test_position_guidance_moves_high_and_low_text_vertically():
    analyzer = FrameAnalyzer(stable_required_frames=1, text_confidence_threshold=0.55)

    high = analyzer.analyze_capture(_capture(image=_document_image(y1=2, y2=32)))
    low = analyzer.analyze_capture(_capture(image=_document_image(y1=128, y2=158)))

    assert high.position_hint == "move_down"
    assert "نزل" in high.guidance
    assert low.position_hint == "move_up"
    assert "ارفع" in low.guidance


def test_centered_text_can_be_ready_to_capture():
    analyzer = FrameAnalyzer(stable_required_frames=1, text_confidence_threshold=0.55)

    result = analyzer.analyze_capture(_capture(image=_document_image()))

    assert result.centered is True
    assert result.position_hint == "centered"
    assert result.ready_to_capture is True


def test_stability_resets_while_text_is_off_center():
    analyzer = FrameAnalyzer(stable_required_frames=2, text_confidence_threshold=0.55)

    off_center = analyzer.analyze_capture(_capture(image=_document_image(x1=5, x2=55)))
    first_centered = analyzer.analyze_capture(_capture(image=_document_image()))
    second_centered = analyzer.analyze_capture(_capture(image=_document_image()))

    assert off_center.stable_frames == 0
    assert first_centered.ready_to_capture is False
    assert first_centered.stable_frames == 1
    assert second_centered.ready_to_capture is True


def test_position_analysis_ignores_dark_background_touching_edges():
    analyzer = FrameAnalyzer(stable_required_frames=1, text_confidence_threshold=0.55)

    result = analyzer.analyze_capture(_capture(image=_paper_on_dark_table_with_center_text()))

    assert result.position_hint == "centered"
    assert result.size_hint != "move_farther"
    assert result.ready_to_capture is True
