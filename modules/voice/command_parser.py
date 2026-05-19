"""Deterministic fixed-command parser for Phase 8."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import unicodedata

from modules.voice.command_models import (
    CommandConfidence,
    CommandError,
    CommandErrorCode,
    CommandIntent,
    CommandPath,
    CommandRequest,
    CommandResult,
    normalize_command_language,
)


DEFAULT_COMMAND_CATALOG: dict[CommandIntent, tuple[str, ...]] = {
    CommandIntent.READ: (
        "read text",
        "read the text",
        "start reading",
        "اقرا النص",
        "اقرأ النص",
        "ابدأ القراءة",
        "ابدا القراءه",
    ),
    CommandIntent.STOP: ("stop", "stop reading", "توقف", "اوقف", "اوقف القراءة"),
    CommandIntent.CONTINUE: ("continue", "resume", "تابع", "استمر", "اكمل"),
    CommandIntent.REPEAT_SENTENCE: (
        "repeat sentence",
        "repeat last sentence",
        "اعد الجمله",
        "اعد الجملة",
        "كرر الجمله",
    ),
    CommandIntent.REPEAT_PARAGRAPH: (
        "repeat paragraph",
        "repeat last paragraph",
        "اعد الفقره",
        "اعد الفقرة",
        "كرر الفقره",
    ),
    CommandIntent.HELP: ("help", "commands", "مساعدة", "الاوامر"),
}

DEFAULT_COMMAND_CATALOG.update(
    {
        CommandIntent.TRANSLATE_TO_ARABIC: (
            "translate to arabic",
            "translate arabic",
            "translate into arabic",
            "translate this to arabic",
            "ترجم الى العربية",
            "ترجم إلى العربية",
            "ترجم للعربية",
        ),
        CommandIntent.TRANSLATE_TO_ENGLISH: (
            "translate to english",
            "translate english",
            "translate into english",
            "translate this to english",
            "ترجم الى الانجليزية",
            "ترجم إلى الإنجليزية",
            "ترجم للانجليزية",
        ),
    }
)

TARGET_LANGUAGE_BY_INTENT = {
    CommandIntent.TRANSLATE_TO_ARABIC: "ar",
    CommandIntent.TRANSLATE_TO_ENGLISH: "en",
}


def normalize_command_phrase(phrase: str) -> str:
    """Normalize fixed-command transcript text without retaining it."""
    value = unicodedata.normalize("NFKD", phrase or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    value = value.replace("ى", "ي").replace("ة", "ه")
    value = re.sub(r"[،؛؟]", " ", value)
    value = re.sub(r"[^\w\s\u0600-\u06FF]", " ", value, flags=re.UNICODE)
    value = re.sub(r"[_\d]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


@dataclass
class CommandParser:
    """Deterministic parser for curated Arabic and English commands."""

    catalog: dict[CommandIntent, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_COMMAND_CATALOG)
    )
    name: str = "command_parser"

    def __post_init__(self) -> None:
        self._normalized_catalog: dict[CommandIntent, set[str]] = {
            intent: {normalize_command_phrase(phrase) for phrase in phrases}
            for intent, phrases in self.catalog.items()
        }

    def parse(self, request: CommandRequest) -> CommandResult:
        """Parse a command request into a single safe intent or guidance."""
        return self.parse_text(request.phrase, language_hint=request.language_hint)

    def parse_text(self, phrase: str, language_hint: str = "unknown") -> CommandResult:
        """Parse transcript text into a command result."""
        language = normalize_command_language(language_hint)
        normalized = normalize_command_phrase(phrase)
        if not normalized:
            return _failure(
                intent=CommandIntent.UNKNOWN,
                language=language,
                code=CommandErrorCode.NO_COMMAND_INPUT,
                confidence=CommandConfidence.NONE,
                guidance="No command was heard. Try saying help.",
            )

        matches = [
            intent
            for intent, phrases in self._normalized_catalog.items()
            if normalized in phrases
        ]
        if len(matches) > 1:
            return _failure(
                intent=CommandIntent.AMBIGUOUS,
                language=language,
                code=CommandErrorCode.AMBIGUOUS_COMMAND,
                confidence=CommandConfidence.AMBIGUOUS,
                guidance="That command was ambiguous. Please say one command clearly.",
            )
        if not matches:
            return _failure(
                intent=CommandIntent.UNKNOWN,
                language=language,
                code=CommandErrorCode.UNKNOWN_COMMAND,
                confidence=CommandConfidence.NONE,
                guidance="Command not recognized. Say help for supported commands.",
            )

        intent = matches[0]
        target_language = TARGET_LANGUAGE_BY_INTENT.get(intent)
        return CommandResult.recognized(
            intent=intent,
            language=language,
            path=CommandPath.PARSER,
            target_language=target_language,
            guidance=_guidance_for_intent(intent),
        )


def _failure(
    *,
    intent: CommandIntent,
    language: str,
    code: CommandErrorCode,
    confidence: CommandConfidence,
    guidance: str,
) -> CommandResult:
    return CommandResult.failure(
        intent=intent,
        language=language,
        path=CommandPath.PARSER,
        confidence=confidence,
        error=CommandError(code=code, message=guidance, recognizer_name="command_parser"),
        guidance=guidance,
    )


def _guidance_for_intent(intent: CommandIntent) -> str:
    if intent == CommandIntent.HELP:
        return "You can say read text, stop, continue, repeat sentence, repeat paragraph, translate to Arabic, or translate to English."
    if intent in {
        CommandIntent.TRANSLATE_TO_ARABIC,
        CommandIntent.TRANSLATE_TO_ENGLISH,
    }:
        return "Translation command recognized."
    return "Command recognized."


__all__ = [
    "CommandParser",
    "DEFAULT_COMMAND_CATALOG",
    "TARGET_LANGUAGE_BY_INTENT",
    "normalize_command_phrase",
]
