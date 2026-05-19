"""Local Vosk fixed-command fallback boundary for Phase 8."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any

from modules.voice.command_models import (
    CommandError,
    CommandErrorCode,
    CommandIntent,
    CommandPath,
    CommandRequest,
    CommandResult,
)
from modules.voice.command_parser import CommandParser


ResourceLoader = Callable[[], Any]
LocalTranscriptProvider = Callable[[CommandRequest, Any], str]


@dataclass
class VoskFallbackRecognizer:
    """Local Vosk fixed-command fallback with lazy resource loading."""

    parser: CommandParser | None = None
    resource_loader: ResourceLoader | None = None
    transcript_provider: LocalTranscriptProvider | None = None
    name: str = "vosk_fallback"
    path: CommandPath = CommandPath.LOCAL
    _resources: Any | None = None

    def recognize(self, request: CommandRequest) -> CommandResult:
        started = time.monotonic()
        if not request.allow_local:
            return self._failure(
                request,
                CommandErrorCode.LOCAL_STT_UNAVAILABLE,
                "Local command recognition is disabled.",
                started,
            )
        try:
            resources = self._load_resources()
        except ImportError:
            return self._failure(
                request,
                CommandErrorCode.LOCAL_STT_UNAVAILABLE,
                "Local Vosk command recognition is not installed.",
                started,
            )
        except Exception as exc:
            return self._failure(
                request,
                CommandErrorCode.LOCAL_STT_UNAVAILABLE,
                f"Local command resources could not load: {type(exc).__name__}",
                started,
            )
        if resources is None:
            return self._failure(
                request,
                CommandErrorCode.LOCAL_STT_UNAVAILABLE,
                "Local command model is not configured.",
                started,
            )
        try:
            transcript = (
                self.transcript_provider(request, resources)
                if self.transcript_provider is not None
                else request.phrase
            )
        except Exception as exc:
            return self._failure(
                request,
                CommandErrorCode.LOCAL_STT_FAILED,
                f"Local command recognition failed: {type(exc).__name__}",
                started,
            )
        parser = self.parser or CommandParser()
        result = parser.parse_text(transcript, language_hint=request.language_hint)
        return result.with_updates(path=self.path, duration_ms=_duration_ms(started))

    def _load_resources(self) -> Any:
        if self._resources is not None:
            return self._resources
        if self.resource_loader is not None:
            self._resources = self.resource_loader()
            return self._resources
        try:
            import vosk  # noqa: F401
        except ImportError:
            raise
        self._resources = {"vosk": True}
        return self._resources

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


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


__all__ = [
    "VoskFallbackRecognizer",
]
