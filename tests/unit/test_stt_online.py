"""Tests for Phase 8 online STT boundary."""

from __future__ import annotations

from modules.voice.command_models import (
    CommandErrorCode,
    CommandIntent,
    CommandRequest,
)
from modules.voice.command_parser import CommandParser
from modules.voice.stt_online import MockCommandRecognizer, OnlineSTTRecognizer, recognize_safely


def test_online_stt_unavailable_when_online_disallowed() -> None:
    recognizer = OnlineSTTRecognizer(parser=CommandParser())

    result = recognizer.recognize(CommandRequest(phrase="read text", allow_online=False))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.ONLINE_STT_UNAVAILABLE


def test_online_stt_maps_provider_exceptions_to_structured_failure() -> None:
    recognizer = MockCommandRecognizer(raise_on_recognize=RuntimeError("down"))

    result = recognize_safely(recognizer, CommandRequest(phrase="read text"))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.ONLINE_STT_FAILED
    assert "read text" not in str(result.safe_metadata)


def test_online_stt_no_supported_command_output_is_structured() -> None:
    recognizer = OnlineSTTRecognizer(
        parser=CommandParser(),
        transcript_provider=lambda request: "private unknown command",
    )

    result = recognizer.recognize(CommandRequest(phrase="ignored"))

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
    assert result.error is not None
    assert result.error.code == CommandErrorCode.UNKNOWN_COMMAND
    assert "private unknown command" not in str(result.safe_metadata)


def test_online_stt_timeout_and_provider_failure_are_structured() -> None:
    timeout = OnlineSTTRecognizer(
        parser=CommandParser(),
        transcript_provider=lambda request: (_ for _ in ()).throw(TimeoutError("slow")),
    )
    failure = OnlineSTTRecognizer(
        parser=CommandParser(),
        transcript_provider=lambda request: (_ for _ in ()).throw(RuntimeError("down")),
    )

    timeout_result = timeout.recognize(CommandRequest(phrase="read text"))
    failure_result = failure.recognize(CommandRequest(phrase="read text"))

    assert timeout_result.error and timeout_result.error.code == CommandErrorCode.ONLINE_STT_FAILED
    assert failure_result.error and failure_result.error.code == CommandErrorCode.ONLINE_STT_FAILED
