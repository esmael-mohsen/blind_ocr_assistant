"""Deterministic bilingual command parser for the voice assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
import unicodedata

from modules.voice.command_catalog import COMMAND_CATALOG
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


DEFAULT_COMMAND_CATALOG = COMMAND_CATALOG
TARGET_LANGUAGE_BY_INTENT = {
    CommandIntent.TRANSLATE_TO_ARABIC: "ar",
    CommandIntent.TRANSLATE_TO_ENGLISH: "en",
}
STRICT_INTENTS = {CommandIntent.EXIT}
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
TRANSLATION_HINTS = {"translate", "translation", "ترجم", "ترجمة"}


def normalize_command_phrase(phrase: str) -> str:
    """Normalize Arabic/English fixed-command transcript text."""
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
    """Parser for curated Arabic and English commands."""

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
        """Parse a command request into a safe intent."""
        return self.parse_text(request.phrase, language_hint=request.language_hint)

    def parse_text(self, phrase: str, language_hint: str = "unknown") -> CommandResult:
        """Parse transcript text into a command result."""
        language = self._resolve_language(phrase, language_hint)
        normalized = normalize_command_phrase(phrase)
        if not normalized:
            return _failure(
                intent=CommandIntent.UNKNOWN,
                language=language,
                code=CommandErrorCode.NO_COMMAND_INPUT,
                confidence=CommandConfidence.NONE,
                guidance=_guidance_for_failure(language),
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
                guidance=_guidance_for_ambiguous(language),
            )
        if matches:
            return _recognized(matches[0], language=language)

        if _looks_like_missing_translation_target(normalized):
            return _failure(
                intent=CommandIntent.UNKNOWN,
                language=language,
                code=CommandErrorCode.UNKNOWN_COMMAND,
                confidence=CommandConfidence.NONE,
                guidance=_translation_target_guidance(language),
            )

        if self._looks_like_mixed_known_commands(normalized):
            return _failure(
                intent=CommandIntent.UNKNOWN,
                language=language,
                code=CommandErrorCode.UNKNOWN_COMMAND,
                confidence=CommandConfidence.NONE,
                guidance=_guidance_for_failure(language),
            )

        fuzzy = self._fuzzy_match(normalized)
        if fuzzy is not None:
            intent, confidence = fuzzy
            return _recognized(
                intent,
                language=language,
                confidence=confidence,
                fallback_used=True,
            )

        return _failure(
            intent=CommandIntent.UNKNOWN,
            language=language,
            code=CommandErrorCode.UNKNOWN_COMMAND,
            confidence=CommandConfidence.NONE,
            guidance=_guidance_for_failure(language),
        )

    def _resolve_language(self, phrase: str, language_hint: str) -> str:
        hinted = normalize_command_language(language_hint)
        if hinted in {"ar", "en", "mixed"}:
            return hinted
        return "ar" if ARABIC_RE.search(phrase or "") else "en"

    def _fuzzy_match(
        self,
        normalized: str,
    ) -> tuple[CommandIntent, CommandConfidence] | None:
        if len(normalized) < 4:
            return None
        best: tuple[CommandIntent, float] | None = None
        for intent, phrases in self._normalized_catalog.items():
            for alias in phrases:
                if not alias:
                    continue
                ratio = SequenceMatcher(None, normalized, alias).ratio()
                tokens = set(normalized.split())
                alias_tokens = set(alias.split())
                overlap = (
                    len(tokens & alias_tokens) / max(1, len(alias_tokens))
                    if tokens and alias_tokens
                    else 0.0
                )
                score = max(ratio, overlap * 0.92)
                if best is None or score > best[1]:
                    best = (intent, score)
        if best is None:
            return None
        threshold = 0.97 if best[0] in STRICT_INTENTS else 0.82
        if best[1] < threshold:
            return None
        confidence = CommandConfidence.HIGH if best[1] >= 0.90 else CommandConfidence.LOW
        return best[0], confidence

    def _looks_like_mixed_known_commands(self, normalized: str) -> bool:
        tokens = normalized.split()
        if len(tokens) < 2:
            return False
        matched_intents = set()
        for token in tokens:
            for intent, phrases in self._normalized_catalog.items():
                if token in phrases:
                    matched_intents.add(intent)
        return len(matched_intents) > 1


def _recognized(
    intent: CommandIntent,
    *,
    language: str,
    confidence: CommandConfidence = CommandConfidence.HIGH,
    fallback_used: bool = False,
) -> CommandResult:
    return CommandResult.recognized(
        intent=intent,
        language=language,
        path=CommandPath.PARSER,
        target_language=TARGET_LANGUAGE_BY_INTENT.get(intent),
        guidance=_guidance_for_intent(intent, language),
        confidence=confidence,
        fallback_used=fallback_used,
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
        error=CommandError(
            code=code,
            message=guidance,
            recognizer_name="command_parser",
        ),
        guidance=guidance,
    )


def _looks_like_missing_translation_target(normalized: str) -> bool:
    tokens = set(normalized.split())
    has_translation = bool(tokens & TRANSLATION_HINTS)
    has_target = bool(
        tokens
        & {
            "arabic",
            "english",
            "عربي",
            "العربي",
            "العربيه",
            "انجليزي",
            "الانجليزي",
            "الانجليزيه",
            "انجلش",
        }
    )
    return has_translation and not has_target


def _guidance_for_failure(language: str) -> str:
    if language == "ar":
        return "قول: اقرأ، ترجم، توقف."
    return "Say: read text, translate, or stop."


def _guidance_for_ambiguous(language: str) -> str:
    if language == "ar":
        return "الأمر مش واضح. قول أمر واحد."
    return "That was ambiguous. Say one command."


def _translation_target_guidance(language: str) -> str:
    if language == "ar":
        return "عربي ولا إنجليزي؟"
    return "Arabic or English?"


def _guidance_for_intent(intent: CommandIntent, language: str) -> str:
    arabic = language == "ar"
    if intent == CommandIntent.HELP:
        return (
            "تقدر تقول: اقرأ، ترجم عربي، ترجم إنجليزي، توقف، كمل."
            if arabic
            else "Say: read text, translate to Arabic, translate to English, stop, or continue."
        )
    if intent == CommandIntent.CANCEL:
        return "تم الإلغاء." if arabic else "Cancelled."
    if intent == CommandIntent.STATUS:
        return "هقولك الحالة." if arabic else "Checking status."
    if intent == CommandIntent.WHAT_DO_YOU_SEE:
        return "هراجع الصورة." if arabic else "Checking the camera view."
    if intent == CommandIntent.REPEAT_GUIDANCE:
        return "هعيد التوجيه." if arabic else "Repeating guidance."
    if intent == CommandIntent.READ_AGAIN:
        return "هعيد القراءة." if arabic else "Reading again."
    if intent == CommandIntent.CAPTURE_NOW:
        return "بصور دلوقتي." if arabic else "Capturing now."
    if intent == CommandIntent.SWITCH_ARABIC:
        return "تم تفعيل العربي." if arabic else "Arabic enabled."
    if intent == CommandIntent.SWITCH_ENGLISH:
        return "English enabled." if not arabic else "تم تفعيل الإنجليزي."
    if intent == CommandIntent.EXIT:
        return "تأكيد الخروج." if arabic else "Exit command recognized."
    if intent == CommandIntent.QUIET_MODE:
        return "هقلل الكلام." if arabic else "Quiet mode enabled."
    if intent == CommandIntent.VERBOSE_MODE:
        return "هشرح أكتر." if arabic else "Verbose guidance enabled."
    if intent == CommandIntent.VOICE_TEST:
        return "هختبر الصوت." if arabic else "Testing voice."
    if intent in {
        CommandIntent.TRANSLATE_TO_ARABIC,
        CommandIntent.TRANSLATE_TO_ENGLISH,
    }:
        return "بترجم." if arabic else "Translating."
    if intent == CommandIntent.READ:
        return "تمام، بقرأ." if arabic else "Reading."
    if intent == CommandIntent.STOP:
        return "توقفت." if arabic else "Stopped."
    if intent == CommandIntent.CONTINUE:
        return "هكمل." if arabic else "Continuing."
    if intent == CommandIntent.REPEAT_SENTENCE:
        return "هعيد الجملة." if arabic else "Repeating sentence."
    if intent == CommandIntent.REPEAT_PARAGRAPH:
        return "هعيد الفقرة." if arabic else "Repeating paragraph."
    return "تم." if arabic else "Command recognized."


__all__ = [
    "CommandParser",
    "DEFAULT_COMMAND_CATALOG",
    "TARGET_LANGUAGE_BY_INTENT",
    "normalize_command_phrase",
]
