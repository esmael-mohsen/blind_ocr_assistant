"""Tests for the Phase 7 online translation stack (Google -> MyMemory)."""

from __future__ import annotations

from modules.assistant.translation_controller import TranslationController
from modules.translation.argos_fallback import ArgosTranslateFallback
from modules.translation.online_translation_stack import (
    GoogleTranslatorEngine,
    MyMemoryTranslatorEngine,
    OnlineFallbackTranslationEngine,
)
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationRequest,
)


def _request(*, allow_online: bool = True) -> TranslationRequest:
    return TranslationRequest(
        source_text="مرحبا",
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
        allow_online=allow_online,
    )


def test_google_allow_online_false_returns_unavailable_without_calling_translator() -> None:
    calls: list[tuple[str, str, str]] = []

    def translate_func(text: str, source: str, target: str) -> str:
        calls.append((text, source, target))
        return "Hello"

    engine = GoogleTranslatorEngine(translate_func=translate_func)

    result = engine.translate(_request(allow_online=False))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ONLINE_TRANSLATION_UNAVAILABLE
    assert calls == []


def test_google_success_maps_translated_text_and_language_codes() -> None:
    calls: list[tuple[str, str, str]] = []

    def translate_func(text: str, source: str, target: str) -> str:
        calls.append((text, source, target))
        return "Hello"

    engine = GoogleTranslatorEngine(translate_func=translate_func)
    result = engine.translate(_request())

    assert result.success is True
    assert result.translated_text == "Hello"
    assert calls == [("مرحبا", "ar", "en")]
    assert "Hello" not in str(result.safe_metadata)


def test_online_fallback_uses_mymemory_when_google_raises_timeout() -> None:
    google_calls: list[str] = []
    mymemory_calls: list[str] = []

    def google_translate(text: str, source: str, target: str) -> str:
        google_calls.append(text)
        raise TimeoutError("slow")

    def mymemory_translate(text: str, source: str, target: str) -> str:
        mymemory_calls.append(text)
        return "Hello"

    stack = OnlineFallbackTranslationEngine(
        primary=GoogleTranslatorEngine(translate_func=google_translate),
        backup=MyMemoryTranslatorEngine(translate_func=mymemory_translate),
    )

    result = stack.translate(_request())

    assert result.success is True
    assert result.engine_name == "mymemory_translator"
    assert google_calls == ["مرحبا"]
    assert mymemory_calls == ["مرحبا"]


def test_long_text_is_split_into_chunks_safely() -> None:
    calls: list[str] = []

    def translate_func(text: str, source: str, target: str) -> str:
        calls.append(text)
        return "Hello"

    engine = GoogleTranslatorEngine(translate_func=translate_func, max_chars_per_request=10)
    request = TranslationRequest(
        source_text="مرحبا " * 20,
        source_language=TranslationLanguage.ARABIC,
        target_language=TranslationLanguage.ENGLISH,
    )

    result = engine.translate(request)

    assert result.success is True
    assert len(calls) > 1


def test_full_stack_google_then_mymemory_then_argos_offline() -> None:
    def google_translate(text: str, source: str, target: str) -> str:
        raise TimeoutError("down")

    def mymemory_translate(text: str, source: str, target: str) -> str:
        raise RuntimeError("blocked")

    class _Translation:
        def translate(self, text: str) -> str:
            return "Hello"

    class _Language:
        def __init__(self, code: str):
            self.code = code

        def get_translation(self, target):
            return _Translation()

    offline = ArgosTranslateFallback(language_loader=lambda: [_Language("ar"), _Language("en")])
    online = OnlineFallbackTranslationEngine(
        primary=GoogleTranslatorEngine(translate_func=google_translate),
        backup=MyMemoryTranslatorEngine(translate_func=mymemory_translate),
    )
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest(
        "مرحبا",
        target_language="en",
        source_language="ar",
        explicit_source_language=True,
    )

    assert result.success is True
    assert result.path.value == "offline"
    assert result.fallback_used is True


def test_all_translators_failed_returns_structured_failure() -> None:
    def google_translate(text: str, source: str, target: str) -> str:
        raise TimeoutError("down")

    def mymemory_translate(text: str, source: str, target: str) -> str:
        raise RuntimeError("blocked")

    offline = ArgosTranslateFallback(language_loader=lambda: [])
    online = OnlineFallbackTranslationEngine(
        primary=GoogleTranslatorEngine(translate_func=google_translate),
        backup=MyMemoryTranslatorEngine(translate_func=mymemory_translate),
    )
    controller = TranslationController(online_engine=online, offline_engine=offline)

    result = controller.translate_latest(
        "مرحبا",
        target_language="en",
        source_language="ar",
        explicit_source_language=True,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == TranslationErrorCode.ALL_TRANSLATION_PROVIDERS_FAILED
