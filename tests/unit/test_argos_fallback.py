"""Tests for the Phase 7 Argos Translate fallback."""

from __future__ import annotations

from modules.translation.argos_fallback import ArgosTranslateFallback
from modules.translation.translation_models import (
    TranslationErrorCode,
    TranslationLanguage,
    TranslationPath,
    TranslationRequest,
)


class FakeTranslation:
    def __init__(self, output: str | Exception) -> None:
        self.output = output

    def translate(self, text: str) -> str:
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


class FakeLanguage:
    def __init__(self, code: str, translations: dict[str, FakeTranslation] | None = None):
        self.code = code
        self._translations = translations or {}

    def get_translation(self, target: "FakeLanguage") -> FakeTranslation | None:
        return self._translations.get(target.code)


def _request() -> TranslationRequest:
    return TranslationRequest(
        source_text="Hello",
        source_language=TranslationLanguage.ENGLISH,
        target_language=TranslationLanguage.ARABIC,
        allow_online=False,
        allow_offline=True,
    )


def test_argos_fallback_lazy_loads_package() -> None:
    calls: list[str] = []

    def loader():
        calls.append("loaded")
        ar = FakeLanguage("ar")
        en = FakeLanguage("en", {"ar": FakeTranslation("مرحبا")})
        return [en, ar]

    fallback = ArgosTranslateFallback(language_loader=loader)

    assert calls == []
    result = fallback.translate(_request())

    assert result.success is True
    assert result.path == TranslationPath.OFFLINE
    assert result.translated_text == "مرحبا"
    assert calls == ["loaded"]


def test_missing_package_missing_model_and_translation_failure_are_structured() -> None:
    missing_package = ArgosTranslateFallback(
        language_loader=lambda: (_ for _ in ()).throw(ImportError("missing"))
    )
    missing_model = ArgosTranslateFallback(
        language_loader=lambda: [FakeLanguage("en"), FakeLanguage("ar")]
    )
    failing_model = ArgosTranslateFallback(
        language_loader=lambda: [
            FakeLanguage("en", {"ar": FakeTranslation(RuntimeError("boom"))}),
            FakeLanguage("ar"),
        ]
    )

    results = [
        missing_package.translate(_request()),
        missing_model.translate(_request()),
        failing_model.translate(_request()),
    ]

    assert [result.success for result in results] == [False, False, False]
    assert results[0].error and results[0].error.code == TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE
    assert results[1].error and results[1].error.code == TranslationErrorCode.OFFLINE_TRANSLATION_UNAVAILABLE
    assert results[2].error and results[2].error.code == TranslationErrorCode.OFFLINE_TRANSLATION_FAILED
    for result in results:
        assert "Hello" not in str(result.safe_metadata)
