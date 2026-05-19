"""Dialogue manager for Phase 8 voice command routing."""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.voice.command_models import (
    CommandConfidence,
    CommandError,
    CommandErrorCode,
    CommandIntent,
    CommandPath,
    CommandRequest,
    CommandResult,
    DialogueState,
)
from modules.voice.command_parser import CommandParser
from modules.voice.stt_online import recognize_safely


@dataclass
class DialogueManager:
    """Stateful command router for fixed voice commands."""

    reading_controller: object | None = None
    translation_controller: object | None = None
    parser: CommandParser = field(default_factory=CommandParser)
    online_recognizer: object | None = None
    local_recognizer: object | None = None
    latest_clean_text: str = ""
    latest_language: str = "mixed"
    state: DialogueState = field(default_factory=DialogueState)

    def get_state(self) -> DialogueState:
        """Return latest safe command state."""
        return self.state

    def handle_command(
        self,
        phrase: str,
        language_hint: str = "unknown",
        allow_online: bool = True,
        allow_local: bool = True,
    ) -> CommandResult:
        """Recognize and route one fixed command attempt."""
        request = CommandRequest(
            phrase=phrase,
            language_hint=language_hint,
            allow_online=allow_online,
            allow_local=allow_local,
        )
        result = self._recognize(request)
        routed = self._route_result(result)
        self.state = self.state.with_result(routed)
        return routed

    def _recognize(self, request: CommandRequest) -> CommandResult:
        has_recognizers = self.online_recognizer is not None or self.local_recognizer is not None
        if not has_recognizers:
            return self.parser.parse(request)

        online_result: CommandResult | None = None
        if request.allow_online and self.online_recognizer is not None:
            online_result = recognize_safely(self.online_recognizer, request)
            if online_result.success:
                return online_result
        elif not request.allow_online:
            online_result = CommandResult.failure(
                intent=CommandIntent.UNKNOWN,
                language=request.language_hint,
                path=CommandPath.ONLINE,
                error=CommandError(
                    code=CommandErrorCode.ONLINE_STT_UNAVAILABLE,
                    message="Online speech recognition is disabled.",
                ),
                guidance="Online speech recognition is disabled.",
            )

        if request.allow_local and self.local_recognizer is not None:
            local_result = recognize_safely(self.local_recognizer, request).with_updates(
                fallback_used=True
            )
            if local_result.success:
                return local_result
            if online_result is not None:
                return self._all_recognizers_failed(request, local_result)
            return local_result

        if online_result is not None:
            return online_result

        return self.parser.parse(request)

    def _route_result(self, result: CommandResult) -> CommandResult:
        if not result.success:
            return result
        if result.intent == CommandIntent.READ:
            return self._route_read(result)
        if result.intent == CommandIntent.STOP:
            return self._route_reading_control(result, "stop", "Reading stopped.")
        if result.intent == CommandIntent.CONTINUE:
            return self._route_reading_control(
                result,
                "continue_reading",
                "Continuing reading.",
            )
        if result.intent == CommandIntent.REPEAT_SENTENCE:
            return self._route_reading_control(
                result,
                "repeat_last_sentence",
                "Repeating the last sentence.",
            )
        if result.intent == CommandIntent.REPEAT_PARAGRAPH:
            return self._route_reading_control(
                result,
                "repeat_last_paragraph",
                "Repeating the last paragraph.",
            )
        if result.intent in {
            CommandIntent.TRANSLATE_TO_ARABIC,
            CommandIntent.TRANSLATE_TO_ENGLISH,
        }:
            return self._route_translation(result)
        if result.intent == CommandIntent.HELP:
            return result.with_updates(
                guidance=(
                    "You can say read text, stop, continue, repeat sentence, "
                    "repeat paragraph, translate to Arabic, or translate to English."
                )
            )
        return result

    @staticmethod
    def _all_recognizers_failed(
        request: CommandRequest,
        latest_result: CommandResult,
    ) -> CommandResult:
        return CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language=request.language_hint,
            path=latest_result.path,
            fallback_used=True,
            confidence=latest_result.confidence,
            error=CommandError(
                code=CommandErrorCode.ALL_RECOGNIZERS_FAILED,
                message="All command recognizers failed.",
            ),
            guidance="Command recognition failed. Try again with one short supported command.",
        )

    def _route_read(self, result: CommandResult) -> CommandResult:
        text = self.latest_clean_text.strip()
        if not text or self.reading_controller is None:
            return self._routing_failure(
                result,
                guidance="No readable text is available yet.",
            )
        try:
            speech_result = self.reading_controller.start_reading(
                text,
                language=self.latest_language,
            )
            success = bool(getattr(speech_result, "success", False))
        except Exception:
            success = False
        if not success:
            return self._routing_failure(
                result,
                guidance="Reading could not start.",
            )
        return result.with_updates(
            routed=True,
            routed_success=True,
            confidence=CommandConfidence.HIGH,
            guidance="Reading is starting.",
        )

    def _route_reading_control(
        self,
        result: CommandResult,
        method_name: str,
        success_guidance: str,
    ) -> CommandResult:
        if self.reading_controller is None or not hasattr(
            self.reading_controller,
            method_name,
        ):
            return self._routing_failure(
                result,
                guidance="There is no reading to control.",
            )
        try:
            control_result = getattr(self.reading_controller, method_name)()
            success = bool(getattr(control_result, "success", False))
        except Exception:
            success = False
        if not success:
            return self._routing_failure(
                result,
                guidance="The reading command could not be completed.",
                code=CommandErrorCode.COMMAND_ROUTING_FAILED,
            )
        return result.with_updates(
            routed=True,
            routed_success=True,
            confidence=CommandConfidence.HIGH,
            guidance=success_guidance,
        )

    def _route_translation(self, result: CommandResult) -> CommandResult:
        text = self.latest_clean_text.strip()
        if not text:
            return self._routing_failure(
                result,
                guidance="No readable text is available to translate.",
            )
        if self.translation_controller is None:
            return self._routing_failure(
                result,
                guidance="Translation is not available.",
            )

        target_language = result.target_language
        if target_language is None:
            target_language = (
                "ar"
                if result.intent == CommandIntent.TRANSLATE_TO_ARABIC
                else "en"
            )
        try:
            translation_result = self.translation_controller.translate_latest(
                text,
                target_language,
                source_language=self.latest_language,
            )
            success = bool(getattr(translation_result, "success", False))
        except Exception:
            success = False

        if not success:
            return self._routing_failure(
                result,
                guidance="Translation command could not be completed.",
                code=CommandErrorCode.COMMAND_ROUTING_FAILED,
            )

        return result.with_updates(
            routed=True,
            routed_success=True,
            confidence=CommandConfidence.HIGH,
            target_language=target_language,
            guidance="Translation is starting.",
        )

    @staticmethod
    def _routing_failure(
        result: CommandResult,
        *,
        guidance: str,
        code: CommandErrorCode = CommandErrorCode.ROUTING_TARGET_UNAVAILABLE,
    ) -> CommandResult:
        return CommandResult.failure(
            intent=result.intent,
            language=result.language,
            path=result.path,
            fallback_used=result.fallback_used,
            confidence=result.confidence,
            target_language=result.target_language,
            routed=False,
            routed_success=False,
            error=CommandError(code=code, message=guidance),
            guidance=guidance,
        )


__all__ = [
    "DialogueManager",
]
