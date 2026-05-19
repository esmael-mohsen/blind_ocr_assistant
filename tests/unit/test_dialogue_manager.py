"""Tests for Phase 8 dialogue manager command routing."""

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
        self.stopped = False
        self.continued = False
        self.repeated_sentences = 0
        self.repeated_paragraphs = 0

    def start_reading(self, clean_text: str, language: str = "mixed"):
        self.start_calls.append((clean_text, language))
        return type("SpeechResult", (), {"success": True})()

    def stop(self):
        self.stopped = True
        return type("SpeechResult", (), {"success": True})()

    def continue_reading(self):
        self.continued = True
        return type("SpeechResult", (), {"success": True})()

    def repeat_last_sentence(self):
        self.repeated_sentences += 1
        return type("SpeechResult", (), {"success": True})()

    def repeat_last_paragraph(self):
        self.repeated_paragraphs += 1
        return type("SpeechResult", (), {"success": True})()


class DummyTranslationController:
    def __init__(self, *, success: bool = True) -> None:
        self.success = success
        self.calls: list[tuple[str, str]] = []

    def translate_latest(self, clean_text: str, target_language: str, **kwargs):
        self.calls.append((clean_text, target_language))
        return type("TranslationResult", (), {"success": self.success})()


def test_read_command_with_latest_clean_text_routes_to_reading() -> None:
    reader = DummyReadingController()
    manager = DialogueManager(
        reading_controller=reader,
        latest_clean_text="Clean private text.",
        latest_language="en",
    )

    result = manager.handle_command("read text", language_hint="en")

    assert result.success is True
    assert result.intent == CommandIntent.READ
    assert result.routed is True
    assert result.routed_success is True
    assert reader.start_calls == [("Clean private text.", "en")]
    assert "reading" in result.guidance.lower()


def test_arabic_read_command_routes_with_arabic_guidance() -> None:
    reader = DummyReadingController()
    manager = DialogueManager(
        reading_controller=reader,
        latest_clean_text="نص جاهز.",
        latest_language="ar",
    )

    result = manager.handle_command("اقرا النص", language_hint="ar")

    assert result.success is True
    assert result.intent == CommandIntent.READ
    assert reader.start_calls == [("نص جاهز.", "ar")]
    assert result.language == "ar"


def test_read_command_without_latest_text_returns_guidance_without_reading_call() -> None:
    reader = DummyReadingController()
    manager = DialogueManager(reading_controller=reader)

    result = manager.handle_command("read text", language_hint="en")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.ROUTING_TARGET_UNAVAILABLE
    assert reader.start_calls == []
    assert "no readable text" in result.guidance.lower()


def test_latest_dialogue_state_replaces_only_safe_metadata() -> None:
    manager = DialogueManager(
        reading_controller=DummyReadingController(),
        latest_clean_text="First private text.",
        latest_language="en",
    )

    first = manager.handle_command("read text", language_hint="en")
    manager.latest_clean_text = "Second private text."
    second = manager.handle_command("read text", language_hint="en")

    state = manager.get_state()
    assert first.success is True
    assert second.success is True
    assert state.last_intent == CommandIntent.READ
    assert "First private text" not in str(state.safe_metadata)
    assert "Second private text" not in str(state.safe_metadata)


def test_online_disabled_uses_local_fallback_for_read_command() -> None:
    local = MockCommandRecognizer(
        path=CommandPath.LOCAL,
        result=CommandResult.recognized(
            intent=CommandIntent.READ,
            language="en",
            path=CommandPath.LOCAL,
            guidance="Command recognized.",
        ),
    )
    manager = DialogueManager(
        reading_controller=DummyReadingController(),
        local_recognizer=local,
        latest_clean_text="Clean text.",
        latest_language="en",
    )

    result = manager.handle_command("read text", language_hint="en", allow_online=False)

    assert result.success is True
    assert result.path == CommandPath.LOCAL
    assert result.fallback_used is True
    assert len(local.calls) == 1


def test_online_failure_unknown_and_timeout_use_local_fallback() -> None:
    online_results = [
        MockCommandRecognizer(
            result=CommandResult.failure(
                intent=CommandIntent.UNKNOWN,
                language="en",
                path=CommandPath.ONLINE,
                error=CommandError(
                    code=CommandErrorCode.ONLINE_STT_UNAVAILABLE,
                    message="online unavailable",
                ),
                guidance="online unavailable",
            )
        ),
        MockCommandRecognizer(raise_on_recognize=TimeoutError("slow")),
        MockCommandRecognizer(
            result=CommandResult.failure(
                intent=CommandIntent.UNKNOWN,
                language="en",
                path=CommandPath.ONLINE,
                error=CommandError(
                    code=CommandErrorCode.UNKNOWN_COMMAND,
                    message="no supported command",
                ),
                guidance="unknown",
            )
        ),
    ]
    for online in online_results:
        local = MockCommandRecognizer(
            path=CommandPath.LOCAL,
            result=CommandResult.recognized(
                intent=CommandIntent.READ,
                language="en",
                path=CommandPath.LOCAL,
                guidance="Command recognized.",
            ),
        )
        manager = DialogueManager(
            reading_controller=DummyReadingController(),
            online_recognizer=online,
            local_recognizer=local,
            latest_clean_text="Clean text.",
            latest_language="en",
        )

        result = manager.handle_command("read text", language_hint="en")

        assert result.success is True
        assert result.path == CommandPath.LOCAL
        assert result.fallback_used is True
        assert len(local.calls) == 1


def test_local_disallowed_returns_online_failure_without_local_call() -> None:
    online = MockCommandRecognizer(
        result=CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language="en",
            path=CommandPath.ONLINE,
            error=CommandError(
                code=CommandErrorCode.UNKNOWN_COMMAND,
                message="unknown",
            ),
            guidance="unknown",
        )
    )
    local = MockCommandRecognizer(path=CommandPath.LOCAL)
    manager = DialogueManager(online_recognizer=online, local_recognizer=local)

    result = manager.handle_command("unknown", language_hint="en", allow_local=False)

    assert result.success is False
    assert result.error and result.error.code == CommandErrorCode.UNKNOWN_COMMAND
    assert local.calls == []


def test_all_recognizers_fail_returns_structured_guidance() -> None:
    online = MockCommandRecognizer(raise_on_recognize=RuntimeError("online"))
    local = MockCommandRecognizer(
        path=CommandPath.LOCAL,
        raise_on_recognize=RuntimeError("local"),
    )
    manager = DialogueManager(online_recognizer=online, local_recognizer=local)

    result = manager.handle_command("read text", language_hint="en")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.ALL_RECOGNIZERS_FAILED
    assert "try again" in result.guidance.lower()


def test_playback_commands_route_to_reading_controls() -> None:
    reader = DummyReadingController()
    manager = DialogueManager(reading_controller=reader)

    stop = manager.handle_command("stop", language_hint="en")
    cont = manager.handle_command("continue", language_hint="en")
    sentence = manager.handle_command("repeat sentence", language_hint="en")
    paragraph = manager.handle_command("repeat paragraph", language_hint="en")

    assert stop.success is True
    assert cont.success is True
    assert sentence.success is True
    assert paragraph.success is True
    assert reader.stopped is True
    assert reader.continued is True
    assert reader.repeated_sentences == 1
    assert reader.repeated_paragraphs == 1


def test_playback_commands_without_reading_controller_return_guidance() -> None:
    manager = DialogueManager()

    result = manager.handle_command("continue", language_hint="en")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.ROUTING_TARGET_UNAVAILABLE
    assert "no reading" in result.guidance.lower()


def test_ambiguous_playback_phrase_does_not_route() -> None:
    reader = DummyReadingController()
    manager = DialogueManager(reading_controller=reader)

    result = manager.handle_command("stop continue", language_hint="en")

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
    assert reader.stopped is False
    assert reader.continued is False


def test_translation_commands_route_with_target_language() -> None:
    translator = DummyTranslationController()
    manager = DialogueManager(
        translation_controller=translator,
        latest_clean_text="Clean text.",
        latest_language="en",
    )

    to_ar = manager.handle_command("translate to Arabic", language_hint="en")
    to_en = manager.handle_command("translate to English", language_hint="en")

    assert to_ar.success is True
    assert to_ar.intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert to_ar.target_language == "ar"
    assert to_en.success is True
    assert to_en.intent == CommandIntent.TRANSLATE_TO_ENGLISH
    assert to_en.target_language == "en"
    assert translator.calls == [("Clean text.", "ar"), ("Clean text.", "en")]


def test_translation_command_requires_latest_text_and_translation_boundary() -> None:
    no_text = DialogueManager(translation_controller=DummyTranslationController())
    no_boundary = DialogueManager(latest_clean_text="Clean text.")

    missing_text = no_text.handle_command("translate to Arabic", language_hint="en")
    missing_boundary = no_boundary.handle_command(
        "translate to Arabic",
        language_hint="en",
    )

    assert missing_text.success is False
    assert missing_text.error and missing_text.error.code == CommandErrorCode.ROUTING_TARGET_UNAVAILABLE
    assert "no readable text" in missing_text.guidance.lower()
    assert missing_boundary.success is False
    assert missing_boundary.error and missing_boundary.error.code == CommandErrorCode.ROUTING_TARGET_UNAVAILABLE


def test_translation_failure_returns_guidance() -> None:
    translator = DummyTranslationController(success=False)
    manager = DialogueManager(
        translation_controller=translator,
        latest_clean_text="Clean text.",
    )

    result = manager.handle_command("translate to Arabic", language_hint="en")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == CommandErrorCode.COMMAND_ROUTING_FAILED
    assert "translation" in result.guidance.lower()


def test_help_command_returns_examples_without_routing_actions() -> None:
    reader = DummyReadingController()
    translator = DummyTranslationController()
    manager = DialogueManager(
        reading_controller=reader,
        translation_controller=translator,
        latest_clean_text="Clean text.",
    )

    result = manager.handle_command("help", language_hint="en")

    assert result.success is True
    assert result.intent == CommandIntent.HELP
    assert result.routed is False
    assert "read text" in result.guidance.lower()
    assert reader.start_calls == []
    assert translator.calls == []
