"""Tests for Phase 6 TTS data models."""

from __future__ import annotations

import pytest

from modules.voice.voice_models import (
    DEFAULT_SPEECH_RATE_WPM,
    MAX_SPEECH_RATE_WPM,
    MIN_SPEECH_RATE_WPM,
    ReadingControlCommand,
    ReadingControlType,
    ReadingState,
    SegmentType,
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
    TextSegment,
    clamp_speech_rate,
    sanitize_speech_metadata,
)


def test_speech_rate_clamps_to_phase6_bounds() -> None:
    assert clamp_speech_rate(None) == DEFAULT_SPEECH_RATE_WPM
    assert clamp_speech_rate(20) == MIN_SPEECH_RATE_WPM
    assert clamp_speech_rate(300) == MAX_SPEECH_RATE_WPM
    assert clamp_speech_rate(175) == 175


def test_speech_request_normalizes_rate_and_safe_metadata() -> None:
    request = SpeechRequest(
        text="Private medicine instruction",
        language="en",
        rate_wpm=999,
        operation=SpeechOperation.READ_ALL,
        segment_type=SegmentType.FULL_TEXT,
        segment_order=0,
    )

    assert request.rate_wpm == MAX_SPEECH_RATE_WPM
    assert request.safe_metadata["operation"] == "read_all"
    assert request.safe_metadata["text_length"] == len("Private medicine instruction")
    assert "text" not in request.safe_metadata


def test_speech_request_rejects_empty_speak_text() -> None:
    with pytest.raises(ValueError, match="text is required"):
        SpeechRequest(text="   ")


def test_speech_result_failure_requires_error() -> None:
    with pytest.raises(ValueError, match="error is required"):
        SpeechResult.failure(operation=SpeechOperation.READ_ALL)


def test_speech_result_safe_metadata_excludes_guidance_and_text() -> None:
    error = TTSError(
        code=TTSErrorCode.TTS_ENGINE_FAILURE,
        message="engine failed",
        engine_name="mock",
    )
    result = SpeechResult.failure(
        operation=SpeechOperation.READ_ALL,
        engine_name="mock",
        error=error,
        guidance="Could not read the text.",
    )

    assert result.success is False
    assert result.safe_metadata["error_code"] == "TTS_ENGINE_FAILURE"
    assert "guidance" not in result.safe_metadata
    assert "text" not in result.safe_metadata


def test_text_segment_has_stable_safe_metadata_without_text() -> None:
    segment = TextSegment(
        segment_id="doc1:sentence:0",
        segment_type=SegmentType.SENTENCE,
        order=0,
        text="First private sentence.",
        language="en",
        parent_text_id="doc1",
    )

    assert segment.safe_metadata["segment_id"] == "doc1:sentence:0"
    assert segment.safe_metadata["segment_type"] == "sentence"
    assert segment.safe_metadata["text_length"] == len("First private sentence.")
    assert "text" not in segment.safe_metadata


def test_reading_state_defaults_are_inactive_and_private() -> None:
    state = ReadingState()

    assert state.is_active is False
    assert state.is_paused is False
    assert state.current_rate_wpm == DEFAULT_SPEECH_RATE_WPM
    assert "current_segment" not in state.safe_metadata
    assert state.safe_metadata["is_active"] is False


def test_reading_control_command_clamps_rate() -> None:
    command = ReadingControlCommand(
        command_type=ReadingControlType.SET_RATE,
        requested_rate_wpm=30,
    )

    assert command.requested_rate_wpm == MIN_SPEECH_RATE_WPM
    assert command.safe_metadata["command_type"] == "set_rate"


def test_sanitize_speech_metadata_removes_sensitive_keys() -> None:
    assert sanitize_speech_metadata(
        {
            "text": "secret",
            "spoken_text": "secret",
            "snippet": "secret",
            "operation": SpeechOperation.STOP,
        }
    ) == {"operation": "stop"}
