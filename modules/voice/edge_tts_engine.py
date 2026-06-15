"""Natural online TTS adapter backed by Microsoft Edge neural voices."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from modules.voice.voice_models import (
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
)


SynthesizeFunc = Callable[[SpeechRequest, str, Path], None]
PlayFunc = Callable[[Path, float], None]


@dataclass
class EdgeTTSEngine:
    """Free online-first TTS engine using edge-tts with local playback."""

    arabic_voice: str = "ar-EG-SalmaNeural"
    english_voice: str = "en-US-JennyNeural"
    timeout_seconds: float = 60.0
    synthesize_func: SynthesizeFunc | None = None
    play_func: PlayFunc | None = None
    retry_no_audio_count: int = 1
    name: str = "edge_tts"
    supports_pause: bool = False
    supports_resume: bool = False

    def speak(self, request: SpeechRequest) -> SpeechResult:
        started = time.monotonic()
        output_path = Path(tempfile.gettempdir()) / f"blind_ocr_tts_{time.time_ns()}.mp3"
        voice = self._voice_for_language(request.language)
        try:
            attempts = max(1, self.retry_no_audio_count + 1)
            for attempt in range(attempts):
                try:
                    if self.synthesize_func is not None:
                        self.synthesize_func(request, voice, output_path)
                    else:
                        asyncio.run(self._synthesize(request, voice, output_path))
                    break
                except Exception as exc:
                    output_path.unlink(missing_ok=True)
                    if attempt < attempts - 1 and _is_no_audio_received(exc):
                        continue
                    raise
            player = self.play_func or _play_media_file
            player(output_path, self._timeout_for_request(request))
        except ImportError:
            return self._failure(
                request.operation,
                TTSErrorCode.TTS_ENGINE_UNAVAILABLE,
                "edge-tts is not installed.",
            )
        except FileNotFoundError as exc:
            return self._failure(
                request.operation,
                TTSErrorCode.TTS_ENGINE_UNAVAILABLE,
                str(exc),
            )
        except Exception as exc:
            return self._failure(
                request.operation,
                TTSErrorCode.TTS_ENGINE_FAILURE,
                f"Edge TTS failed: {type(exc).__name__}",
            )
        finally:
            output_path.unlink(missing_ok=True)

        return SpeechResult.ok(
            operation=request.operation,
            engine_name=self.name,
            duration_ms=int((time.monotonic() - started) * 1000),
            guidance="Reading started.",
        )

    def stop(self) -> SpeechResult:
        return SpeechResult.ok(
            operation=SpeechOperation.STOP,
            engine_name=self.name,
            guidance="Reading stopped.",
        )

    def pause(self) -> SpeechResult:
        return self._failure(
            SpeechOperation.PAUSE,
            TTSErrorCode.TTS_PAUSE_UNSUPPORTED,
            "Pause is not supported by Edge TTS playback.",
        )

    def resume(self) -> SpeechResult:
        return self._failure(
            SpeechOperation.CONTINUE,
            TTSErrorCode.TTS_RESUME_UNSUPPORTED,
            "Resume is not supported by Edge TTS playback.",
        )

    async def _synthesize(
        self,
        request: SpeechRequest,
        voice: str,
        output_path: Path,
    ) -> None:
        try:
            import edge_tts
        except ImportError:
            raise
        communicate = edge_tts.Communicate(request.text, voice)
        await communicate.save(str(output_path))

    def _voice_for_language(self, language: str) -> str:
        normalized = (language or "").lower()
        if normalized.startswith("ar"):
            return self.arabic_voice
        return self.english_voice

    def _timeout_for_request(self, request: SpeechRequest) -> float:
        words = max(1, len(str(request.text or "").split()))
        rate_wpm = max(80, int(request.rate_wpm or 150))
        estimated_seconds = (words / rate_wpm) * 60.0
        return max(self.timeout_seconds, estimated_seconds + 30.0)

    def _failure(
        self,
        operation: SpeechOperation,
        code: TTSErrorCode,
        message: str,
    ) -> SpeechResult:
        return SpeechResult.failure(
            operation=operation,
            engine_name=self.name,
            error=TTSError(code=code, message=message, engine_name=self.name),
            guidance=message,
        )


def _play_media_file(path: Path, timeout_seconds: float) -> None:
    """Play an MP3 file with platform tools when available."""
    failures: list[str] = []
    if shutil.which("ffplay"):
        completed = subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            check=False,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return
        failures.append(f"ffplay:{completed.returncode}")
    if shutil.which("mpg123"):
        completed = subprocess.run(
            ["mpg123", "-q", str(path)],
            check=False,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return
        failures.append(f"mpg123:{completed.returncode}")
    if shutil.which("powershell"):
        command = (
            "Add-Type -AssemblyName PresentationCore; "
            "$player = New-Object System.Windows.Media.MediaPlayer; "
            f"$player.Open([Uri]::new('{path.as_posix()}')); "
            "$player.Play(); "
            "Start-Sleep -Milliseconds 500; "
            "while ($player.NaturalDuration.HasTimeSpan -and "
            "$player.Position -lt $player.NaturalDuration.TimeSpan) "
            "{ Start-Sleep -Milliseconds 100 }"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            timeout=timeout_seconds,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return
        failures.append(f"powershell:{completed.returncode}")
    if failures:
        raise RuntimeError("MP3 playback failed: " + ", ".join(failures))
    raise FileNotFoundError("No MP3 playback tool was found.")


def _is_no_audio_received(exc: BaseException) -> bool:
    return "NoAudioReceived" in f"{type(exc).__name__} {exc}"


__all__ = ["EdgeTTSEngine"]
