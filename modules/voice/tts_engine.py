"""Text-to-speech engine boundary for Phase 6."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Protocol

from modules.voice.voice_models import (
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
    clamp_speech_rate,
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


def _resolve_scoop_shim_target(executable_path: Path) -> Path | None:
    shim_path = executable_path.with_suffix(".shim")
    if not shim_path.is_file():
        return None
    try:
        content = shim_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"path\s*=\s*(?:\"(?P<quoted>.+)\"|(?P<raw>.+))$", stripped)
        if not match:
            continue
        raw_path = (match.group("quoted") or match.group("raw") or "").strip()
        if not raw_path:
            continue
        return Path(raw_path)
    return None


def _resolve_executable_path(binary: str) -> Path | None:
    if not binary.strip():
        return None
    candidate = Path(binary)
    if candidate.is_file():
        scoop_target = _resolve_scoop_shim_target(candidate)
        if scoop_target is not None and scoop_target.is_file():
            return scoop_target
        return candidate
    resolved = shutil.which(binary)
    if not resolved:
        return None
    resolved_path = Path(resolved)
    scoop_target = _resolve_scoop_shim_target(resolved_path)
    if scoop_target is not None and scoop_target.is_file():
        return scoop_target
    return resolved_path


def _guess_espeak_data_path(binary_path: Path) -> Path | None:
    candidates = (
        binary_path.parent / "espeak-ng-data",
        binary_path.parent.parent / "espeak-ng-data",
    )
    for candidate in candidates:
        if (candidate / "phontab").is_file() and (candidate / "voices").is_dir():
            return candidate
    return None


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
            env = None
            if not (os.getenv("ESPEAK_DATA_PATH") or os.getenv("ESPEAKNG_DATA_PATH")):
                resolved_binary = _resolve_executable_path(self.binary)
                if resolved_binary is not None:
                    data_path = _guess_espeak_data_path(resolved_binary)
                    if data_path is not None:
                        env = dict(os.environ)
                        env.setdefault("ESPEAK_DATA_PATH", str(data_path))
                        env.setdefault("ESPEAKNG_DATA_PATH", str(data_path))

            run_kwargs: dict[str, object] = {
                "input": request.text,
                "text": True,
                "capture_output": True,
                "timeout": self.timeout_seconds,
                "check": False,
            }
            if env is not None:
                run_kwargs["env"] = env

            completed = self.runner(command, **run_kwargs)
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


@dataclass
class WindowsSapiEngine:
    """Windows built-in speech adapter via System.Speech."""

    timeout_seconds: float = 60.0
    runner: Runner = subprocess.run
    name: str = "windows_sapi"
    supports_pause: bool = False
    supports_resume: bool = False

    def speak(self, request: SpeechRequest) -> SpeechResult:
        started = time.monotonic()
        culture_prefix = self._culture_prefix_for_language(request.language)
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Add-Type -AssemblyName System.Speech; "
                "$text = [Console]::In.ReadToEnd(); "
                "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$culturePrefix = '{culture_prefix}'; "
                "$voice = $speaker.GetInstalledVoices() | "
                "Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name.StartsWith($culturePrefix) } | "
                "Select-Object -First 1; "
                "if ($voice -ne $null) { $speaker.SelectVoice($voice.VoiceInfo.Name); } "
                "elseif ($culturePrefix -eq 'ar') { "
                "Write-Error 'No installed Windows SAPI Arabic voice was found.'; exit 3; "
                "} "
                f"$speaker.Rate = {self._rate_for_request(request.rate_wpm)}; "
                "$speaker.Speak($text);"
            ),
        ]
        try:
            completed = self.runner(
                command,
                input=request.text,
                text=True,
                capture_output=True,
                timeout=self._timeout_for_request(request),
                check=False,
            )
        except FileNotFoundError:
            return self._failure(
                operation=request.operation,
                code=TTSErrorCode.TTS_ENGINE_UNAVAILABLE,
                message="PowerShell/System.Speech is not available.",
                guidance="The Windows speech engine is not available.",
            )
        except subprocess.TimeoutExpired:
            return self._failure(
                operation=request.operation,
                code=TTSErrorCode.TTS_ENGINE_FAILURE,
                message="Windows speech timed out.",
                guidance="The Windows speech engine timed out.",
            )
        except Exception as exc:
            return self._failure(
                operation=request.operation,
                code=TTSErrorCode.TTS_ENGINE_FAILURE,
                message=f"Unexpected Windows speech failure: {type(exc).__name__}",
                guidance="The Windows speech engine failed unexpectedly.",
            )
        duration_ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            return self._failure(
                operation=request.operation,
                code=TTSErrorCode.TTS_ENGINE_UNAVAILABLE
                if completed.returncode == 3
                else TTSErrorCode.TTS_ENGINE_FAILURE,
                message=completed.stderr.strip() or "Windows speech failed.",
                guidance=(
                    "No Windows Arabic voice is installed. Install edge-tts or an Arabic Windows voice."
                    if completed.returncode == 3
                    else "The Windows speech engine could not read the text."
                ),
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
            guidance="Pause is not supported by the Windows speech adapter.",
        )

    def resume(self) -> SpeechResult:
        return _unsupported_result(
            operation=SpeechOperation.CONTINUE,
            engine_name=self.name,
            code=TTSErrorCode.TTS_RESUME_UNSUPPORTED,
            guidance="Continue is not supported by the Windows speech adapter.",
        )

    def _failure(
        self,
        *,
        operation: SpeechOperation,
        code: TTSErrorCode,
        message: str,
        guidance: str,
    ) -> SpeechResult:
        return SpeechResult.failure(
            operation=operation,
            engine_name=self.name,
            error=TTSError(code=code, message=message, engine_name=self.name),
            guidance=guidance,
        )

    def _timeout_for_request(self, request: SpeechRequest) -> float:
        words = max(1, len(str(request.text or "").split()))
        rate_wpm = max(80, int(request.rate_wpm or 150))
        estimated_seconds = (words / rate_wpm) * 60.0
        return max(self.timeout_seconds, estimated_seconds + 30.0)

    @staticmethod
    def _rate_for_request(rate_wpm: int | None) -> int:
        rate = clamp_speech_rate(rate_wpm)
        return max(-10, min(10, int(round((rate - 150) / 7))))

    @staticmethod
    def _culture_prefix_for_language(language: str) -> str:
        normalized = (language or "").strip().lower()
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
    "WindowsSapiEngine",
]
