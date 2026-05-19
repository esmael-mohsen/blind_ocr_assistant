"""Privacy tests for Phase 8 command metadata."""

from __future__ import annotations

from modules.assistant.dialogue_manager import DialogueManager
from modules.voice.command_models import (
    CommandError,
    CommandErrorCode,
    CommandIntent,
    CommandPath,
    CommandResult,
)
from modules.voice.stt_online import MockCommandRecognizer


class DummyReadingController:
    def __init__(self) -> None:
        self.start_calls: list[tuple[str, str]] = []

    def start_reading(self, clean_text: str, language: str = "mixed"):
        self.start_calls.append((clean_text, language))
        return type("SpeechResult", (), {"success": True})()


def test_read_command_metadata_excludes_command_and_clean_text() -> None:
    phrase = "read text"
    clean_text = "Patient name: Private Person. Medicine code 12345."
    manager = DialogueManager(
        reading_controller=DummyReadingController(),
        latest_clean_text=clean_text,
        latest_language="en",
    )

    result = manager.handle_command(phrase, language_hint="en")
    state = manager.get_state()

    metadata_blob = f"{result.safe_metadata} {state.safe_metadata}"
    assert result.success is True
    assert phrase not in metadata_blob
    assert clean_text not in metadata_blob
    assert "Private Person" not in metadata_blob
    assert "Medicine code" not in metadata_blob
    assert "recognized_phrase" not in result.safe_metadata
    assert "clean_text" not in result.safe_metadata


def test_fallback_and_all_recognizer_failure_metadata_exclude_text() -> None:
    phrase = "read text"
    clean_text = "Patient name: Private Person. Medicine code 12345."
    local_success = MockCommandRecognizer(
        path=CommandPath.LOCAL,
        result=CommandResult.recognized(
            intent=CommandIntent.READ,
            language="en",
            path=CommandPath.LOCAL,
            guidance="Command recognized.",
        ),
    )
    fallback = DialogueManager(
        online_recognizer=MockCommandRecognizer(raise_on_recognize=RuntimeError("down")),
        local_recognizer=local_success,
        reading_controller=DummyReadingController(),
        latest_clean_text=clean_text,
        latest_language="en",
    ).handle_command(phrase, language_hint="en")

    failed = DialogueManager(
        online_recognizer=MockCommandRecognizer(raise_on_recognize=RuntimeError("down")),
        local_recognizer=MockCommandRecognizer(
            path=CommandPath.LOCAL,
            result=CommandResult.failure(
                intent=CommandIntent.UNKNOWN,
                language="en",
                path=CommandPath.LOCAL,
                error=CommandError(
                    code=CommandErrorCode.LOCAL_STT_FAILED,
                    message="local failed",
                ),
                guidance="local failed",
            ),
        ),
    ).handle_command(phrase, language_hint="en")

    metadata_blob = f"{fallback.safe_metadata} {failed.safe_metadata}"
    assert fallback.success is True
    assert failed.success is False
    assert phrase not in metadata_blob
    assert clean_text not in metadata_blob
    assert "Private Person" not in metadata_blob
