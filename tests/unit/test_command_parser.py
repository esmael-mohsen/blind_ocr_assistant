"""Tests for deterministic bilingual command parsing."""

from __future__ import annotations

from modules.voice.command_catalog import COMMAND_CATALOG
from modules.voice.command_models import (
    CommandErrorCode,
    CommandIntent,
    CommandPath,
)
from modules.voice.command_parser import CommandParser, normalize_command_phrase


def test_command_catalog_has_bilingual_aliases_without_mojibake() -> None:
    serialized = repr(COMMAND_CATALOG)

    assert "ط§" not in serialized
    for intent, aliases in COMMAND_CATALOG.items():
        if intent in {CommandIntent.UNKNOWN, CommandIntent.AMBIGUOUS}:
            continue
        assert any(any("\u0600" <= char <= "\u06ff" for char in alias) for alias in aliases)
        assert any(alias.isascii() for alias in aliases)


def test_normalize_command_phrase_handles_english_case_spaces_and_punctuation() -> None:
    assert normalize_command_phrase("  READ,   TEXT!! ") == "read text"


def test_normalize_command_phrase_handles_arabic_punctuation_and_diacritics() -> None:
    assert normalize_command_phrase(" أُقْرَأ، النَّص! ") == "اقرا النص"


def test_parser_returns_unknown_for_unmatched_phrase_without_leaking_phrase() -> None:
    parser = CommandParser()

    result = parser.parse_text("private random phrase", language_hint="en")

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
    assert result.error is not None
    assert result.error.code == CommandErrorCode.UNKNOWN_COMMAND
    assert "private random phrase" not in str(result.safe_metadata)


def test_parser_returns_ambiguous_for_multi_intent_phrase() -> None:
    parser = CommandParser(
        catalog={
            CommandIntent.READ: ("read",),
            CommandIntent.STOP: ("read",),
        }
    )

    result = parser.parse_text("read", language_hint="en")

    assert result.success is False
    assert result.intent == CommandIntent.AMBIGUOUS
    assert result.error is not None
    assert result.error.code == CommandErrorCode.AMBIGUOUS_COMMAND


def test_parser_returns_no_command_for_empty_and_noise() -> None:
    parser = CommandParser()

    empty = parser.parse_text("   ", language_hint="en")
    noise = parser.parse_text("!!! ???", language_hint="en")

    assert empty.error and empty.error.code == CommandErrorCode.NO_COMMAND_INPUT
    assert noise.error and noise.error.code == CommandErrorCode.NO_COMMAND_INPUT


def test_parser_handles_help_command_without_routing() -> None:
    parser = CommandParser(catalog={CommandIntent.HELP: ("help", "مساعدة")})

    result = parser.parse_text("help", language_hint="en")

    assert result.success is True
    assert result.intent == CommandIntent.HELP
    assert result.path == CommandPath.PARSER
    assert result.routed is False
    assert "say" in result.guidance.lower()


def test_parser_recognizes_arabic_and_english_read_commands() -> None:
    parser = CommandParser()

    english = parser.parse_text("Read text", language_hint="en")
    arabic = parser.parse_text("اقرأ النص", language_hint="ar")

    assert english.success is True
    assert english.intent == CommandIntent.READ
    assert arabic.success is True
    assert arabic.intent == CommandIntent.READ


def test_parser_recognizes_playback_control_commands() -> None:
    parser = CommandParser()

    assert parser.parse_text("stop", language_hint="en").intent == CommandIntent.STOP
    assert parser.parse_text("continue", language_hint="en").intent == CommandIntent.CONTINUE
    assert (
        parser.parse_text("repeat sentence", language_hint="en").intent
        == CommandIntent.REPEAT_SENTENCE
    )
    assert (
        parser.parse_text("repeat paragraph", language_hint="en").intent
        == CommandIntent.REPEAT_PARAGRAPH
    )
    assert parser.parse_text("توقف", language_hint="ar").intent == CommandIntent.STOP
    assert parser.parse_text("كمل", language_hint="ar").intent == CommandIntent.CONTINUE
    assert (
        parser.parse_text("عيد الجملة", language_hint="ar").intent
        == CommandIntent.REPEAT_SENTENCE
    )
    assert (
        parser.parse_text("عيد الفقرة", language_hint="ar").intent
        == CommandIntent.REPEAT_PARAGRAPH
    )


def test_parser_does_not_route_multi_intent_playback_phrase() -> None:
    parser = CommandParser()

    result = parser.parse_text("stop continue", language_hint="en")

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
    assert result.error is not None
    assert result.error.code == CommandErrorCode.UNKNOWN_COMMAND


def test_parser_recognizes_translation_command_targets() -> None:
    parser = CommandParser()

    to_ar = parser.parse_text("translate to Arabic", language_hint="en")
    to_en = parser.parse_text("translate to English", language_hint="en")
    ar_to_ar = parser.parse_text("ترجم للعربية", language_hint="ar")
    ar_to_en = parser.parse_text("ترجم للانجليزي", language_hint="ar")

    assert to_ar.intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert to_ar.target_language == "ar"
    assert to_en.intent == CommandIntent.TRANSLATE_TO_ENGLISH
    assert to_en.target_language == "en"
    assert ar_to_ar.intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert ar_to_ar.target_language == "ar"
    assert ar_to_en.intent == CommandIntent.TRANSLATE_TO_ENGLISH
    assert ar_to_en.target_language == "en"


def test_parser_recognizes_runtime_management_commands() -> None:
    parser = CommandParser()

    assert parser.parse_text("cancel").intent == CommandIntent.CANCEL
    assert parser.parse_text("status").intent == CommandIntent.STATUS
    assert parser.parse_text("what do you see").intent == CommandIntent.WHAT_DO_YOU_SEE
    assert parser.parse_text("repeat guidance").intent == CommandIntent.REPEAT_GUIDANCE
    assert parser.parse_text("read again").intent == CommandIntent.READ_AGAIN
    assert parser.parse_text("capture now").intent == CommandIntent.CAPTURE_NOW
    assert parser.parse_text("switch arabic").intent == CommandIntent.SWITCH_ARABIC
    assert parser.parse_text("switch english").intent == CommandIntent.SWITCH_ENGLISH
    assert parser.parse_text("quiet mode").intent == CommandIntent.QUIET_MODE
    assert parser.parse_text("verbose mode").intent == CommandIntent.VERBOSE_MODE
    assert parser.parse_text("voice test").intent == CommandIntent.VOICE_TEST
    assert parser.parse_text("exit").intent == CommandIntent.EXIT


def test_parser_uses_limited_fuzzy_matching_for_common_commands() -> None:
    parser = CommandParser()

    result = parser.parse_text("reed text", language_hint="en")

    assert result.success is True
    assert result.intent == CommandIntent.READ
    assert result.fallback_used is True


def test_parser_accepts_common_stt_mishearing_for_start_reading() -> None:
    parser = CommandParser()

    result = parser.parse_text("start treating", language_hint="en")

    assert result.success is True
    assert result.intent == CommandIntent.READ


def test_parser_recognizes_real_arabic_runtime_commands() -> None:
    parser = CommandParser()

    assert parser.parse_text("اقرا النص").intent == CommandIntent.READ
    assert parser.parse_text("اقرالي").intent == CommandIntent.READ
    assert parser.parse_text("اتكلم عربي").intent == CommandIntent.SWITCH_ARABIC
    assert parser.parse_text("ترجم عربي").intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert parser.parse_text("اسكت").intent == CommandIntent.STOP
    assert parser.parse_text("صوت أقل").intent == CommandIntent.QUIET_MODE


def test_parser_asks_for_translation_target_without_executing() -> None:
    parser = CommandParser()

    result = parser.parse_text("ترجم", language_hint="ar")

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
    assert result.error is not None
    assert result.error.code == CommandErrorCode.UNKNOWN_COMMAND
    assert result.guidance == "عربي ولا إنجليزي؟"


def test_parser_does_not_fuzzy_match_exit() -> None:
    parser = CommandParser()

    result = parser.parse_text("exist", language_hint="en")

    assert result.success is False
    assert result.intent == CommandIntent.UNKNOWN
