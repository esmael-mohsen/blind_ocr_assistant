"""Tests for Phase 8 Vosk fallback boundary."""

from __future__ import annotations

from modules.voice.command_models import CommandErrorCode, CommandIntent, CommandRequest
from modules.voice.command_parser import CommandParser
from modules.voice.vosk_fallback import VoskFallbackRecognizer


def test_vosk_fallback_lazy_loads_resources_for_fixed_command_success() -> None:
    calls: list[str] = []

    def loader():
        calls.append("loaded")
        return {"ready": True}

    recognizer = VoskFallbackRecognizer(
        parser=CommandParser(catalog={CommandIntent.HELP: ("help",)}),
        resource_loader=loader,
        transcript_provider=lambda request, resources: "help",
    )

    assert calls == []
    result = recognizer.recognize(CommandRequest(phrase="ignored", allow_local=True))

    assert result.success is True
    assert result.intent == CommandIntent.HELP
    assert calls == ["loaded"]


def test_vosk_fallback_missing_package_missing_model_and_failure_are_structured() -> None:
    request = CommandRequest(phrase="read text", allow_local=True)
    missing_package = VoskFallbackRecognizer(
        resource_loader=lambda: (_ for _ in ()).throw(ImportError("missing")),
    )
    missing_model = VoskFallbackRecognizer(resource_loader=lambda: None)
    failing = VoskFallbackRecognizer(
        resource_loader=lambda: {"ready": True},
        transcript_provider=lambda request, resources: (_ for _ in ()).throw(
            RuntimeError("boom")
        ),
    )

    results = [
        missing_package.recognize(request),
        missing_model.recognize(request),
        failing.recognize(request),
    ]

    assert [result.success for result in results] == [False, False, False]
    assert results[0].error and results[0].error.code == CommandErrorCode.LOCAL_STT_UNAVAILABLE
    assert results[1].error and results[1].error.code == CommandErrorCode.LOCAL_STT_UNAVAILABLE
    assert results[2].error and results[2].error.code == CommandErrorCode.LOCAL_STT_FAILED
    for result in results:
        assert "read text" not in str(result.safe_metadata)
