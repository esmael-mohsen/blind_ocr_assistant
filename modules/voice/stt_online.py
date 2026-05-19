"""Optional online STT boundary for Phase 8."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import time
from typing import Protocol

from modules.voice.command_models import (
    CommandError,
    CommandErrorCode,
    CommandIntent,
    CommandPath,
    CommandRequest,
    CommandResult,
)
from modules.voice.command_parser import CommandParser


class CommandRecognizer(Protocol):
    """Protocol for replaceable command recognizers."""

    name: str
    path: CommandPath

    def recognize(self, request: CommandRequest) -> CommandResult:
        """Recognize a command request or return structured guidance."""


TranscriptProvider = Callable[[CommandRequest], str]


@dataclass
class MockCommandRecognizer:
    """Deterministic recognizer for dialogue-manager tests."""

    name: str = "mock_recognizer"
    path: CommandPath = CommandPath.ONLINE
    result: CommandResult | None = None
    raise_on_recognize: Exception | None = None
    calls: list[CommandRequest] = field(default_factory=list)

    def recognize(self, request: CommandRequest) -> CommandResult:
        self.calls.append(request)
        if self.raise_on_recognize is not None:
            raise self.raise_on_recognize
        if self.result is not None:
            return self.result
        return CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language=request.language_hint,
            path=self.path,
            error=CommandError(
                code=CommandErrorCode.UNKNOWN_COMMAND,
                message="mock recognizer did not match a command",
                recognizer_name=self.name,
            ),
            guidance="Command not recognized.",
        )


@dataclass
class OnlineSTTRecognizer:
    """Optional online STT boundary that parses returned transcripts."""

    parser: CommandParser
    transcript_provider: TranscriptProvider | None = None
    timeout_exceptions: tuple[type[BaseException], ...] = (TimeoutError,)
    name: str = "online_stt"
    path: CommandPath = CommandPath.ONLINE

    def recognize(self, request: CommandRequest) -> CommandResult:
        started = time.monotonic()
        if not request.allow_online or self.transcript_provider is None:
            return self._failure(
                request,
                CommandErrorCode.ONLINE_STT_UNAVAILABLE,
                "Online speech recognition is unavailable.",
                started,
            )
        try:
            transcript = self.transcript_provider(request)
        except self.timeout_exceptions:
            return self._failure(
                request,
                CommandErrorCode.ONLINE_STT_FAILED,
                "Online speech recognition timed out.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                CommandErrorCode.ONLINE_STT_FAILED,
                f"Online speech recognition failed: {type(exc).__name__}",
                started,
            )

        result = self.parser.parse_text(transcript, language_hint=request.language_hint)
        return result.with_updates(path=self.path, duration_ms=_duration_ms(started))

    def _failure(
        self,
        request: CommandRequest,
        code: CommandErrorCode,
        message: str,
        started: float,
    ) -> CommandResult:
        return CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language=request.language_hint,
            path=self.path,
            duration_ms=_duration_ms(started),
            error=CommandError(code=code, message=message, recognizer_name=self.name),
            guidance=message,
        )


def recognize_safely(
    recognizer: CommandRecognizer,
    request: CommandRequest,
) -> CommandResult:
    """Call a recognizer and convert exceptions to structured results."""
    started = time.monotonic()
    try:
        return recognizer.recognize(request)
    except Exception as exc:
        path = getattr(recognizer, "path", CommandPath.ONLINE)
        code = (
            CommandErrorCode.ONLINE_STT_FAILED
            if path == CommandPath.ONLINE
            else CommandErrorCode.LOCAL_STT_FAILED
        )
        return CommandResult.failure(
            intent=CommandIntent.UNKNOWN,
            language=request.language_hint,
            path=path,
            duration_ms=_duration_ms(started),
            error=CommandError(
                code=code,
                message=f"recognizer raised {type(exc).__name__}",
                recognizer_name=getattr(recognizer, "name", None),
            ),
            guidance="Speech recognition failed unexpectedly.",
        )


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


__all__ = [
    "CommandRecognizer",
    "MockCommandRecognizer",
    "OnlineSTTRecognizer",
    "recognize_safely",
]
