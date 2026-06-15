"""Tests for Phase 6 TTS engine boundary."""

from __future__ import annotations

import subprocess
from unittest.mock import Mock

from modules.voice.tts_engine import EspeakNGEngine, MockTTSEngine
from modules.voice.edge_tts_engine import EdgeTTSEngine, _play_media_file
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


def test_windows_sapi_selects_voice_by_language() -> None:
    runner = Mock(return_value=subprocess.CompletedProcess(args=[], returncode=0))
    engine = __import__("modules.voice.tts_engine", fromlist=["WindowsSapiEngine"]).WindowsSapiEngine(
        runner=runner
    )

    result = engine.speak(SpeechRequest(text="مرحبا", language="ar"))

    assert result.success is True
    command = runner.call_args.args[0]
    assert "$culturePrefix = 'ar';" in command[-1]
    assert "GetInstalledVoices" in command[-1]


def test_windows_sapi_reports_missing_arabic_voice_as_unavailable() -> None:
    runner = Mock(
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=3,
            stderr="No installed Windows SAPI Arabic voice was found.",
        )
    )
    engine = __import__("modules.voice.tts_engine", fromlist=["WindowsSapiEngine"]).WindowsSapiEngine(
        runner=runner
    )

    result = engine.speak(SpeechRequest(text="مرحبا", language="ar"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.TTS_ENGINE_UNAVAILABLE
    assert "Arabic voice" in result.guidance


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


def test_edge_tts_uses_language_specific_voice_and_injected_io(tmp_path) -> None:
    calls = []

    def synthesize(request, voice, output_path):
        calls.append(("synthesize", voice, request.language))
        output_path.write_bytes(b"audio")

    def play(path, timeout):
        calls.append(("play", path.exists(), timeout))

    engine = EdgeTTSEngine(
        arabic_voice="ar-EG-Test",
        english_voice="en-US-Test",
        synthesize_func=synthesize,
        play_func=play,
    )

    result = engine.speak(SpeechRequest(text="hello", language="ar"))

    assert result.success is True
    assert calls[0] == ("synthesize", "ar-EG-Test", "ar")
    assert calls[1][0] == "play"


def test_edge_tts_extends_playback_timeout_for_long_text(tmp_path) -> None:
    calls = []

    def synthesize(_request, _voice, output_path):
        output_path.write_bytes(b"audio")

    def play(_path, timeout):
        calls.append(timeout)

    engine = EdgeTTSEngine(
        timeout_seconds=10.0,
        synthesize_func=synthesize,
        play_func=play,
    )
    long_text = " ".join(["word"] * 600)

    result = engine.speak(SpeechRequest(text=long_text, language="en", rate_wpm=120))

    assert result.success is True
    assert calls[0] > 10.0


def test_edge_tts_failure_is_structured() -> None:
    engine = EdgeTTSEngine(
        synthesize_func=lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
        play_func=lambda *_args: None,
    )

    result = engine.speak(SpeechRequest(text="hello", language="en"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TTSErrorCode.TTS_ENGINE_FAILURE


def test_edge_tts_retries_no_audio_received_once(tmp_path) -> None:
    calls = []

    def synthesize(_request, _voice, output_path):
        calls.append("synthesize")
        if len(calls) == 1:
            raise RuntimeError("NoAudioReceived")
        output_path.write_bytes(b"audio")

    engine = EdgeTTSEngine(
        synthesize_func=synthesize,
        play_func=lambda *_args: calls.append("play"),
    )

    result = engine.speak(SpeechRequest(text="مرحبا", language="ar"))

    assert result.success is True
    assert calls == ["synthesize", "synthesize", "play"]


def test_edge_tts_player_falls_back_when_first_player_fails(monkeypatch, tmp_path) -> None:
    audio = tmp_path / "voice.mp3"
    audio.write_bytes(b"audio")
    calls = []

    def which(binary):
        return binary if binary in {"ffplay", "powershell"} else None

    def run(command, **_kwargs):
        calls.append(command[0])
        return subprocess.CompletedProcess(
            args=command,
            returncode=1 if command[0] == "ffplay" else 0,
        )

    monkeypatch.setattr("modules.voice.edge_tts_engine.shutil.which", which)
    monkeypatch.setattr("modules.voice.edge_tts_engine.subprocess.run", run)

    _play_media_file(audio, 1.0)

    assert calls == ["ffplay", "powershell"]
