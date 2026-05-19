"""Tests for Phase 8 command data models."""

from __future__ import annotations

import pytest

from modules.voice.command_models import (
    CommandConfidence,
    CommandError,
    CommandErrorCode,
    CommandFeedback,
    CommandIntent,
    CommandOperation,
    CommandPath,
    CommandRequest,
    CommandResult,
    DialogueState,
    normalize_command_language,
    sanitize_command_metadata,
)


def test_command_request_records_safe_metadata_without_phrase() -> None:
    request = CommandRequest(
        phrase="Read the private medicine text",
        language_hint="en",
        allow_online=True,
        allow_local=True,
        operation=CommandOperation.RECOGNIZE,
    )

    assert request.phrase == "Read the private medicine text"
    assert request.language_hint == "en"
    assert request.safe_metadata["phrase_length"] == len(
        "Read the private medicine text"
    )
    assert "phrase" not in request.safe_metadata
    assert "text" not in request.safe_metadata


def test_command_result_success_and_failure_metadata() -> None:
    result = CommandResult.recognized(
        intent=CommandIntent.READ,
        language="en",
        path=CommandPath.PARSER,
        guidance="Reading is starting.",
        routed=True,
        routed_success=True,
    )

    assert result.success is True
    assert result.safe_metadata["intent"] == "read"
    assert result.safe_metadata["routed"] is True
    assert "guidance" not in result.safe_metadata

    error = CommandError(
        code=CommandErrorCode.UNKNOWN_COMMAND,
        message="unknown",
    )
    failure = CommandResult.failure(
        intent=CommandIntent.UNKNOWN,
        language="en",
        path=CommandPath.PARSER,
        error=error,
        guidance="Try saying read text.",
    )

    assert failure.success is False
    assert failure.safe_metadata["error_code"] == "UNKNOWN_COMMAND"


def test_command_result_failure_requires_error() -> None:
    with pytest.raises(ValueError, match="error is required"):
        CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language="en",
            path=CommandPath.PARSER,
            guidance="Command failed.",
        )


def test_command_error_safe_metadata() -> None:
    error = CommandError(
        code=CommandErrorCode.NO_COMMAND_INPUT,
        message="no command",
        recoverable=False,
        recognizer_name="parser",
    )

    assert error.safe_metadata == {
        "error_code": "NO_COMMAND_INPUT",
        "recoverable": False,
        "recognizer_name": "parser",
    }


def test_dialogue_state_defaults_and_success_update_are_private() -> None:
    state = DialogueState()
    assert state.last_intent is None
    assert state.safe_metadata["has_last_result"] is False

    result = CommandResult.recognized(
        intent=CommandIntent.HELP,
        language="en",
        path=CommandPath.PARSER,
        guidance="You can say read text.",
    )
    updated = state.with_result(result)

    assert updated.last_intent == CommandIntent.HELP
    assert updated.last_guidance == "You can say read text."
    assert updated.safe_metadata["last_intent"] == "help"
    assert "You can say" not in str(updated.safe_metadata)


def test_command_feedback_has_safe_metadata() -> None:
    feedback = CommandFeedback(
        guidance="Say read text.",
        intent=CommandIntent.HELP,
        examples_available=True,
    )

    assert feedback.safe_metadata["intent"] == "help"
    assert feedback.safe_metadata["examples_available"] is True
    assert "guidance" not in feedback.safe_metadata


def test_normalize_command_language_accepts_supported_labels() -> None:
    assert normalize_command_language("arabic") == "ar"
    assert normalize_command_language("English") == "en"
    assert normalize_command_language("mixed") == "mixed"
    assert normalize_command_language(None) == "unknown"


def test_sanitize_command_metadata_removes_sensitive_keys() -> None:
    assert sanitize_command_metadata(
        {
            "raw_speech": "secret",
            "recognized_phrase": "secret",
            "command_snippet": "secret",
            "raw_text": "secret",
            "clean_text": "secret",
            "translated_text": "secret",
            "token": "secret",
            "secret": "secret",
            "intent": CommandIntent.READ,
            "confidence": CommandConfidence.HIGH,
        }
    ) == {"intent": "read", "confidence": "high"}
