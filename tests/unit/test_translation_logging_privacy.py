"""Privacy tests for Phase 7 translation metadata."""

from __future__ import annotations

from modules.assistant.translation_controller import TranslationController
from modules.translation.base import MockTranslationEngine
from modules.translation.translation_models import TranslationPath


def test_successful_translation_metadata_excludes_source_and_translated_text() -> None:
    source_text = "Patient name: Private Person. Medicine code 12345."
    translated_text = "اسم المريض خاص."
    controller = TranslationController(
        online_engine=MockTranslationEngine(responses={("en", "ar"): translated_text})
    )

    result = controller.translate_latest(
        source_text,
        target_language="ar",
        source_language="en",
    )
    state = controller.get_state()

    metadata_blob = f"{result.safe_metadata} {state.safe_metadata}"
    assert result.success is True
    assert source_text not in metadata_blob
    assert translated_text not in metadata_blob
    assert "Private Person" not in metadata_blob
    assert "Medicine code" not in metadata_blob
    assert "Patient name" not in metadata_blob
    assert "translated_text" not in result.safe_metadata
    assert "source_text" not in result.safe_metadata


def test_fallback_and_all_provider_failure_metadata_exclude_text() -> None:
    source_text = "Patient name: Private Person. Medicine code 12345."
    online = MockTranslationEngine(fail_code=None, responses={("en", "ar"): "bad latin"})
    offline = MockTranslationEngine(
        name="offline",
        path=TranslationPath.OFFLINE,
        responses={("en", "ar"): "اسم خاص."},
    )
    controller = TranslationController(online_engine=online, offline_engine=offline)

    fallback = controller.translate_latest(
        source_text,
        target_language="ar",
        source_language="en",
    )

    failed = TranslationController(
        online_engine=MockTranslationEngine(fail_code=None, responses={("en", "ar"): "bad"}),
        offline_engine=MockTranslationEngine(
            path=TranslationPath.OFFLINE,
            responses={("en", "ar"): "bad"},
        ),
    ).translate_latest(source_text, target_language="ar", source_language="en")

    metadata_blob = f"{fallback.safe_metadata} {failed.safe_metadata}"
    assert fallback.success is True
    assert failed.success is False
    assert source_text not in metadata_blob
    assert "Private Person" not in metadata_blob
    assert "Medicine code" not in metadata_blob


def test_safe_metadata_excludes_text_for_noop_direction_and_unsupported_results() -> None:
    source_text = "Patient name: Private Person."
    controller = TranslationController(online_engine=MockTranslationEngine())

    noop = controller.translate_latest(
        source_text,
        target_language="en",
        source_language="en",
        read_result=False,
    )
    direction = controller.translate_latest(
        "Medicine دواء",
        target_language="en",
        source_language="mixed",
    )
    unsupported = controller.translate_latest(
        source_text,
        target_language="fr",
        source_language="en",
    )

    metadata_blob = f"{noop.safe_metadata} {direction.safe_metadata} {unsupported.safe_metadata}"
    assert source_text not in metadata_blob
    assert "Private Person" not in metadata_blob
    assert "Medicine" not in metadata_blob
    assert "دواء" not in metadata_blob
