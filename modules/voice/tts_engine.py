"""Text-to-speech engine boundary for Phase 6."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import subprocess
import time
from typing import Protocol

from modules.voice.voice_models import (
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
)


class TTSEngine(Protocol):
    """Protocol for replaceable TTS engines."""

    name: str
    supports_pause: bool
    supports_resume: bool

    def speak(self, request: SpeechRequest) -> SpeechResult:
        """Speak clean text."""

    def stop(self) -> SpeechResult:
        """Stop current speech if possible."""

    def pause(self) -> SpeechResult:
        """Pause speech when supported."""

    def resume(self) -> SpeechResult:
        """Resume speech when supported."""


@dataclass
class MockTTSEngine:
    """Deterministic in-memory TTS engine for controller tests."""

    name: str = "mock"
    supports_pause: bool = True
    supports_resume: bool = True
    fail_next_speak: bool = False
    spoken_requests: list[SpeechRequest] = field(default_factory=list)
    stopped: bool = False
    paused: bool = False
    resumed: bool = False

    def speak(self, request: SpeechRequest) -> SpeechResult:
        self.spoken_requests.append(request)
        if self.fail_next_speak:
            self.fail_next_speak = False
            return SpeechResult.failure(
                operation=request.operation,
                engine_name=self.name,
                error=TTSError(
                    code=TTSErrorCode.TTS_ENGINE_FAILURE,
                    message="mock speak failure",
                    engine_name=self.name,
                ),
                guidance="The speech engine could not read the text.",
            )
        return SpeechResult.ok(
            operation=request.operation,
            engine_name=self.name,
            guidance="Reading started.",
        )

    def stop(self) -> SpeechResult:
        self.stopped = True
        return SpeechResult.ok(
            operation=SpeechOperation.STOP,
            engine_name=self.name,
            guidance="Reading stopped.",
        )

    def pause(self) -> SpeechResult:
        if not self.supports_pause:
            return _unsupported_result(
                operation=SpeechOperation.PAUSE,
                engine_name=self.name,
                code=TTSErrorCode.TTS_PAUSE_UNSUPPORTED,
                guidance="Pause is not supported by this speech engine.",
            )
        self.paused = True
        return SpeechResult.ok(
            operation=SpeechOperation.PAUSE,
            engine_name=self.name,
            guidance="Reading paused.",
        )

    def resume(self) -> SpeechResult:
        if not self.supports_resume:
            return _unsupported_result(
                operation=SpeechOperation.CONTINUE,
                engine_name=self.name,
                code=TTSErrorCode.TTS_RESUME_UNSUPPORTED,
                guidance="Continue is not supported by this speech engine.",
            )
        self.resumed = True
        return SpeechResult.ok(
            operation=SpeechOperation.CONTINUE,
            engine_name=self.name,
            guidance="Reading continued.",
        )


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass
class EspeakNGEngine:
    """Local eSpeak NG adapter with subprocess errors converted to results."""

    binary: str = "espeak-ng"
    timeout_seconds: float = 30.0
    runner: Runner = subprocess.run
    name: str = "espeak_ng"
    supports_pause: bool = False
    supports_resume: bool = False

    def speak(self, request: SpeechRequest) -> SpeechResult:
        started = time.monotonic()
        command = [
            self.binary,
            "-v",
            self._voice_for_language(request.language),
            "-s",
            str(request.rate_wpm),
        ]
        try:
            completed = self.runner(
                command,
                input=request.text,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return SpeechResult.failure(
                operation=request.operation,
                engine_name=self.name,
                error=TTSError(
                    code=TTSErrorCode.TTS_ENGINE_UNAVAILABLE,
                    message="eSpeak NG executable was not found",
                    engine_name=self.name,
                ),
                guidance="The local speech engine is not installed.",
            )
        except subprocess.TimeoutExpired:
            return self._engine_failure(
                operation=request.operation,
                message="eSpeak NG timed out",
                guidance="The local speech engine timed out.",
            )
        except Exception as exc:
            return self._engine_failure(
                operation=request.operation,
                message=f"Unexpected eSpeak NG failure: {type(exc).__name__}",
                guidance="The local speech engine failed unexpectedly.",
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            return self._engine_failure(
                operation=request.operation,
                message=f"eSpeak NG exited with code {completed.returncode}",
                guidance="The local speech engine could not read the text.",
            )
        return SpeechResult.ok(
            operation=request.operation,
            engine_name=self.name,
            duration_ms=duration_ms,
            guidance="Reading started.",
        )

    def stop(self) -> SpeechResult:
        return SpeechResult.ok(
            operation=SpeechOperation.STOP,
            engine_name=self.name,
            guidance="Reading stopped.",
        )

    def pause(self) -> SpeechResult:
        return _unsupported_result(
            operation=SpeechOperation.PAUSE,
            engine_name=self.name,
            code=TTSErrorCode.TTS_PAUSE_UNSUPPORTED,
            guidance="Pause is not supported by the local speech engine.",
        )

    def resume(self) -> SpeechResult:
        return _unsupported_result(
            operation=SpeechOperation.CONTINUE,
            engine_name=self.name,
            code=TTSErrorCode.TTS_RESUME_UNSUPPORTED,
            guidance="Continue is not supported by the local speech engine.",
        )

    def _engine_failure(
        self,
        *,
        operation: SpeechOperation,
        message: str,
        guidance: str,
    ) -> SpeechResult:
        return SpeechResult.failure(
            operation=operation,
            engine_name=self.name,
            error=TTSError(
                code=TTSErrorCode.TTS_ENGINE_FAILURE,
                message=message,
                engine_name=self.name,
            ),
            guidance=guidance,
        )

    @staticmethod
    def _voice_for_language(language: str) -> str:
        normalized = (language or "mixed").lower()
        if normalized.startswith("ar"):
            return "ar"
        return "en"


def _unsupported_result(
    *,
    operation: SpeechOperation,
    engine_name: str,
    code: TTSErrorCode,
    guidance: str,
) -> SpeechResult:
    return SpeechResult.failure(
        operation=operation,
        engine_name=engine_name,
        error=TTSError(
            code=code,
            message=guidance,
            recoverable=True,
            engine_name=engine_name,
        ),
        guidance=guidance,
    )


__all__ = [
    "EspeakNGEngine",
    "MockTTSEngine",
    "TTSEngine",
]
