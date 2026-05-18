"""Tests for Phase 6 TTS engine boundary."""

from __future__ import annotations

import subprocess
from unittest.mock import Mock

from modules.voice.tts_engine import EspeakNGEngine, MockTTSEngine
from modules.voice.voice_models import (
    SegmentType,
    SpeechOperation,
    SpeechRequest,
    TTSErrorCode,
)


def test_mock_tts_engine_records_requests_without_leaking_text_metadata() -> None:
    engine = MockTTSEngine()
    request = SpeechRequest(text="Private text", operation=SpeechOperation.READ_ALL)

    result = engine.speak(request)

    assert result.success is True
    assert engine.spoken_requests == [request]
    assert "Private text" not in str(result.safe_metadata)


def test_espeak_success_uses_stdin_and_clamped_rate() -> None:
    runner = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0))
    engine = EspeakNGEngine(runner=runner, binary="espeak-ng")
    request = SpeechRequest(
        text="Private text",
        language="en",
        rate_wpm=999,
        operation=SpeechOperation.READ_ALL,
        segment_type=SegmentType.FULL_TEXT,
    )

    result = engine.speak(request)

    assert result.success is True
    args, kwargs = runner.call_args
    assert args[0] == ["espeak-ng", "-v", "en", "-s", "220"]
    assert kwargs["input"] == "Private text"
    assert "Private text" not in str(result.safe_metadata)


def test_espeak_maps_arabic_and_mixed_voices() -> None:
    runner = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0))
    engine = EspeakNGEngine(runner=runner, binary="espeak-ng")

    engine.speak(SpeechRequest(text="نص", language="ar"))
    engine.speak(SpeechRequest(text="Mixed text", language="mixed"))

    assert runner.call_args_list[0].args[0][2] == "ar"
    assert runner.call_args_list[1].args[0][2] == "en"


def test_espeak_unavailable_binary_returns_structured_failure() -> None:
    runner = Mock(side_effect=FileNotFoundError)
    result = EspeakNGEngine(runner=runner).speak(SpeechRequest(text="Text"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.TTS_ENGINE_UNAVAILABLE


def test_espeak_nonzero_exit_returns_engine_failure() -> None:
    runner = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=2))
    result = EspeakNGEngine(runner=runner).speak(SpeechRequest(text="Text"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.TTS_ENGINE_FAILURE


def test_espeak_timeout_returns_engine_failure() -> None:
    runner = Mock(side_effect=subprocess.TimeoutExpired(cmd="espeak-ng", timeout=1))
    result = EspeakNGEngine(runner=runner).speak(SpeechRequest(text="Text"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.TTS_ENGINE_FAILURE


def test_stop_is_idempotent_and_pause_resume_are_structured_unsupported() -> None:
    engine = EspeakNGEngine(runner=Mock())

    stop_result = engine.stop()
    pause_result = engine.pause()
    resume_result = engine.resume()

    assert stop_result.success is True
    assert pause_result.success is False
    assert resume_result.success is False
    assert pause_result.error is not None
    assert resume_result.error is not None
    assert pause_result.error.code == TTSErrorCode.TTS_PAUSE_UNSUPPORTED
    assert resume_result.error.code == TTSErrorCode.TTS_RESUME_UNSUPPORTED


def test_unsupported_pause_resume_results_are_safe_for_controller_fallback() -> None:
    engine = EspeakNGEngine(runner=Mock())

    pause_result = engine.pause()
    resume_result = engine.resume()

    assert pause_result.fallback_used is False
    assert resume_result.fallback_used is False
    assert pause_result.safe_metadata["error_code"] == "TTS_PAUSE_UNSUPPORTED"
    assert resume_result.safe_metadata["error_code"] == "TTS_RESUME_UNSUPPORTED"
