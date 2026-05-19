"""Tests for Phase 7 translation controller behavior."""

from __future__ import annotations

from modules.assistant.translation_controller import TranslationController
from modules.translation.base import MockTranslationEngine
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
)


class DummyReadingController:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def start_reading(self, clean_text: str, language: str = "mixed"):
        self.calls.append((clean_text, language))
        if self.fail:
            return type("SpeechResult", (), {"success": False})()
        return type("SpeechResult", (), {"success": True})()


def test_translate_arabic_to_english_and_hands_to_reading() -> None:
    online = MockTranslationEngine(responses={("ar", "en"): "Take one tablet daily."})
    reader = DummyReadingController()
    controller = TranslationController(online_engine=online, reading_controller=reader)

    result = controller.translate_latest(
        "خذ قرصا واحدا يوميا.",
        target_language="en",
        source_language="ar",
    )

    assert result.success is True
    assert result.translated_text == "Take one tablet daily."
    assert result.source_language == TranslationLanguage.ARABIC
    assert result.target_language == TranslationLanguage.ENGLISH
    assert result.path == TranslationPath.ONLINE
    assert result.reading_handoff_attempted is True
    assert result.reading_handoff_success is True
    assert reader.calls == [("Take one tablet daily.", "en")]
    assert "being read" in result.guidance.lower()


def test_translate_english_to_arabic_without_reading_layer_returns_ready_guidance() -> None:
    online = MockTranslationEngine(responses={("en", "ar"): "خذ قرصا واحدا يوميا."})
    controller = TranslationController(online_engine=online)

    result = controller.translate_latest(
        "Take one tablet daily.",
        target_language="ar",
        source_language="en",
    )

    assert result.success is True
    assert result.translated_text == "خذ قرصا واحدا يوميا."
    assert result.reading_handoff_attempted is False
    assert "ready to read" in result.guidance.lower()


def test_translate_empty_text_returns_guidance_without_provider_calls() -> None:
    online = MockTranslationEngine()
    offline = MockTranslationEngine(path=TranslationPath.OFFLINE)
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest("   ", target_language="en", source_language="ar")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.NO_TEXT_TO_TRANSLATE
    assert online.calls == []
    assert offline.calls == []
    assert "no readable text" in result.guidance.lower()


def test_whitespace_text_does_not_call_any_translation_engine() -> None:
    online = MockTranslationEngine()
    offline = MockTranslationEngine(path=TranslationPath.OFFLINE)
    controller = TranslationController(online_engine=online, offline_engine=offline)

    controller.translate_latest("\n\t ", target_language="ar", source_language="en")

    assert online.calls == []
    assert offline.calls == []


def test_successful_translation_replaces_latest_state() -> None:
    online = MockTranslationEngine(
        responses={
            ("en", "ar"): "مرحبا.",
            ("ar", "en"): "Good morning.",
        }
    )
    controller = TranslationController(online_engine=online)

    first = controller.translate_latest("Hello.", target_language="ar", source_language="en")
    second = controller.translate_latest("صباح الخير.", target_language="en", source_language="ar")

    state = controller.get_state()
    assert first.success is True
    assert second.success is True
    assert state.latest_translated_text == "Good morning."
    assert state.target_language == TranslationLanguage.ENGLISH
    assert "Hello." not in str(state.safe_metadata)
    assert "صباح الخير" not in str(state.safe_metadata)


def test_online_disabled_uses_offline_fallback() -> None:
    online = MockTranslationEngine(responses={("en", "ar"): "should not be called"})
    offline = MockTranslationEngine(
        name="offline",
        path=TranslationPath.OFFLINE,
        responses={("en", "ar"): "مرحبا."},
    )
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest(
        "Hello.",
        target_language="ar",
        source_language="en",
        allow_online=False,
    )

    assert result.success is True
    assert result.path == TranslationPath.OFFLINE
    assert result.fallback_used is True
    assert online.calls == []
    assert len(offline.calls) == 1


def test_online_unavailable_timeout_failure_and_invalid_result_use_offline() -> None:
    cases = [
        None,
        MockTranslationEngine(raise_on_translate=TimeoutError("slow")),
        MockTranslationEngine(fail_code=TranslationErrorCode.ONLINE_TRANSLATION_FAILED),
        MockTranslationEngine(responses={("en", "ar"): "Hello."}),
    ]
    for online in cases:
        offline = MockTranslationEngine(
            name="offline",
            path=TranslationPath.OFFLINE,
            responses={("en", "ar"): "مرحبا."},
        )
        controller = TranslationController(online_engine=online, offline_engine=offline)

        result = controller.translate_latest(
            "Hello.",
            target_language="ar",
            source_language="en",
        )

        assert result.success is True
        assert result.path == TranslationPath.OFFLINE
        assert result.fallback_used is True


def test_offline_disallowed_returns_online_failure_without_fallback() -> None:
    online = MockTranslationEngine(fail_code=TranslationErrorCode.ONLINE_TRANSLATION_FAILED)
    offline = MockTranslationEngine(path=TranslationPath.OFFLINE)
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest(
        "Hello.",
        target_language="ar",
        source_language="en",
        allow_offline=False,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_FAILED
    assert offline.calls == []


def test_all_providers_fail_returns_structured_failure_guidance() -> None:
    online = MockTranslationEngine(fail_code=TranslationErrorCode.ONLINE_TRANSLATION_FAILED)
    offline = MockTranslationEngine(
        path=TranslationPath.OFFLINE,
        fail_code=TranslationErrorCode.OFFLINE_TRANSLATION_FAILED,
    )
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest(
        "Hello.",
        target_language="ar",
        source_language="en",
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ALL_TRANSLATION_PROVIDERS_FAILED
    assert "try again" in result.guidance.lower()


def test_direction_validation_handles_known_unsupported_mixed_and_unknown_sources() -> None:
    online = MockTranslationEngine(responses={("ar", "en"): "Product name."})
    controller = TranslationController(online_engine=online)

    known = controller.translate_latest(
        "اسم المنتج.",
        target_language="en",
        source_language="ar",
    )
    unsupported_source = controller.translate_latest(
        "Bonjour.",
        target_language="en",
        source_language="fr",
    )
    unsupported_target = controller.translate_latest(
        "Hello.",
        target_language="fr",
        source_language="en",
    )
    mixed = controller.translate_latest(
        "Medicine دواء",
        target_language="en",
        source_language="mixed",
    )
    unknown = controller.translate_latest(
        "12345",
        target_language="en",
        source_language="unknown",
    )

    assert known.success is True
    assert unsupported_source.error and unsupported_source.error.code == TranslationErrorCode.UNSUPPORTED_LANGUAGE
    assert unsupported_target.error and unsupported_target.error.code == TranslationErrorCode.UNSUPPORTED_LANGUAGE
    assert mixed.error and mixed.error.code == TranslationErrorCode.LANGUAGE_DIRECTION_REQUIRED
    assert unknown.error and unknown.error.code == TranslationErrorCode.LANGUAGE_DIRECTION_REQUIRED
    assert len(online.calls) == 1


def test_explicit_supported_source_allows_mixed_text_translation() -> None:
    online = MockTranslationEngine(responses={("ar", "en"): "Medicine price."})
    controller = TranslationController(online_engine=online)

    result = controller.translate_latest(
        "دواء price",
        target_language="en",
        source_language="ar",
        explicit_source_language=True,
    )

    assert result.success is True
    assert result.translated_text == "Medicine price."
    assert len(online.calls) == 1


def test_same_language_no_op_preserves_text_and_does_not_call_providers() -> None:
    online = MockTranslationEngine()
    offline = MockTranslationEngine(path=TranslationPath.OFFLINE)
    reader = DummyReadingController()
    controller = TranslationController(
        online_engine=online,
        offline_engine=offline,
        reading_controller=reader,
    )

    result = controller.translate_latest(
        "Clean text to read.",
        target_language="en",
        source_language="en",
    )

    assert result.success is True
    assert result.translated_text == "Clean text to read."
    assert result.path == TranslationPath.NO_OP
    assert result.reading_handoff_attempted is True
    assert result.reading_handoff_success is True
    assert "not needed" in result.guidance.lower()
    assert online.calls == []
    assert offline.calls == []
    assert reader.calls == [("Clean text to read.", "en")]
    assert controller.get_state().latest_translated_text == "Clean text to read."
