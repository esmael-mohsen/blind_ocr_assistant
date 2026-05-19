"""Tests for Phase 8 deterministic command parser."""

from __future__ import annotations

from modules.voice.command_models import (
    CommandErrorCode,
    CommandIntent,
    CommandPath,
)
from modules.voice.command_parser import CommandParser, normalize_command_phrase


def test_normalize_command_phrase_handles_english_case_spaces_and_punctuation() -> None:
    assert normalize_command_phrase("  READ,   TEXT!! ") == "read text"


def test_normalize_command_phrase_handles_arabic_punctuation_and_diacritics() -> None:
    assert normalize_command_phrase(" اِقْرَأ، النَّص! ") == "اقرا النص"


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
    assert parser.parse_text("تابع", language_hint="ar").intent == CommandIntent.CONTINUE
    assert (
        parser.parse_text("اعد الجمله", language_hint="ar").intent
        == CommandIntent.REPEAT_SENTENCE
    )
    assert (
        parser.parse_text("اعد الفقره", language_hint="ar").intent
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
    ar_to_ar = parser.parse_text("ترجم الى العربية", language_hint="ar")
    ar_to_en = parser.parse_text("ترجم الى الانجليزية", language_hint="ar")

    assert to_ar.intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert to_ar.target_language == "ar"
    assert to_en.intent == CommandIntent.TRANSLATE_TO_ENGLISH
    assert to_en.target_language == "en"
    assert ar_to_ar.intent == CommandIntent.TRANSLATE_TO_ARABIC
    assert ar_to_ar.target_language == "ar"
    assert ar_to_en.intent == CommandIntent.TRANSLATE_TO_ENGLISH
    assert ar_to_en.target_language == "en"
