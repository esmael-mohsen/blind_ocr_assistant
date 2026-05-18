"""Tests for the Phase 6 manual TTS smoke-test script."""

from __future__ import annotations

import json

from modules.voice.tts_engine import MockTTSEngine
from modules.voice.voice_models import (
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
)
from scripts import test_tts


def test_tts_script_parses_arguments() -> None:
    args = test_tts.build_parser().parse_args(
        ["--text", "Private text", "--language", "en", "--rate", "175"]
    )

    assert args.text == "Private text"
    assert args.language == "en"
    assert args.rate == 175


def test_tts_script_outputs_structured_success_without_text(capsys) -> None:
    private_text = "Private patient text"
    engine = MockTTSEngine()

    exit_code = test_tts.run_smoke_test(
        ["--text", private_text, "--language", "en"],
        engine_factory=lambda: engine,
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 0
    assert payload["success"] is True
    assert payload["operation"] == "read_all"
    assert private_text not in output


def test_tts_script_outputs_structured_unavailable_failure_without_text(capsys) -> None:
    class UnavailableEngine(MockTTSEngine):
        def speak(self, request: SpeechRequest) -> SpeechResult:
            return SpeechResult.failure(
                operation=SpeechOperation.READ_ALL,
                engine_name=self.name,
                error=TTSError(
                    code=TTSErrorCode.TTS_ENGINE_UNAVAILABLE,
                    message="missing engine",
                    engine_name=self.name,
                ),
                guidance="The local speech engine is unavailable.",
            )

    private_text = "Secret receipt total"

    exit_code = test_tts.run_smoke_test(
        ["--text", private_text, "--language", "en"],
        engine_factory=UnavailableEngine,
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 1
    assert payload["success"] is False
    assert payload["error_code"] == "TTS_ENGINE_UNAVAILABLE"
    assert private_text not in output
