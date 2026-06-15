"""Professional always-on voice command runtime.

This module mirrors the voice assistant architecture used by the companion
currency project: a VoiceManager owns state, a VoiceListener owns audio/STT and
command parsing, and an STT service tries providers in order.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Protocol

try:  # pragma: no cover - optional runtime dependency
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional runtime dependency
    sr = None

from modules.voice.command_models import CommandConfidence, CommandIntent, CommandResult
from modules.voice.command_parser import CommandParser


ListenFunc = Callable[[], str]
SpeakFunc = Callable[[str, str], None]


class VoiceState(str, Enum):
    """Runtime voice session states."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    ACTIVE_SESSION = "ACTIVE_SESSION"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


@dataclass
class VoiceProviderStatus:
    mode: str = "stopped"
    provider: str = "none"
    message: str = "Voice is stopped."


@dataclass(frozen=True)
class AudioPacket:
    """One captured microphone phrase."""

    audio_data: object | None
    raw_data: bytes
    sample_rate: int
    sample_width: int

    @property
    def is_empty(self) -> bool:
        return not self.raw_data


@dataclass(frozen=True)
class STTResult:
    """Provider-level speech-to-text result."""

    text: str
    language: str
    confidence: float
    provider: str
    latency_ms: int


@dataclass(frozen=True)
class ListenerResult:
    """Final voice listener result after STT and command parsing."""

    intent: CommandIntent | None
    raw_text: str
    normalized_text: str
    success: bool
    confidence: CommandConfidence = CommandConfidence.NONE
    stt_provider: str = ""
    stt_latency_ms: int = 0
    guidance: str = ""

    @classmethod
    def from_command_result(
        cls,
        command_result: CommandResult,
        stt_result: STTResult,
        *,
        normalized_text: str,
    ) -> "ListenerResult":
        return cls(
            intent=command_result.intent if command_result.success else None,
            raw_text=stt_result.text,
            normalized_text=normalized_text,
            success=command_result.success,
            confidence=command_result.confidence,
            stt_provider=stt_result.provider,
            stt_latency_ms=stt_result.latency_ms,
            guidance=command_result.guidance,
        )


class AudioInput:
    """Microphone capture with one-time ambient calibration."""

    def __init__(
        self,
        *,
        command_timeout_seconds: float,
        microphone_index: int | None = None,
        sample_rate: int = 16000,
        ambient_noise_duration: float = 0.4,
    ) -> None:
        sr_module = _sr_module()
        if sr_module is None:
            raise RuntimeError("SpeechRecognition is not installed.")
        self._sr = sr_module
        self._recognizer = sr_module.Recognizer()
        self._command_timeout_seconds = command_timeout_seconds
        self._microphone_index = microphone_index
        self._sample_rate = sample_rate
        self._ambient_noise_duration = ambient_noise_duration
        self._calibrated = False

    @property
    def recognizer(self) -> Any:
        return self._recognizer

    def listen(self) -> AudioPacket:
        try:
            microphone = self._sr.Microphone(
                device_index=self._microphone_index,
                sample_rate=self._sample_rate,
            )
        except TypeError:
            try:
                microphone = self._sr.Microphone(device_index=self._microphone_index)
            except TypeError:
                microphone = self._sr.Microphone()
        with microphone as source:
            if not self._calibrated:
                self._recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self._ambient_noise_duration,
                )
                self._calibrated = True
            audio_data = self._recognizer.listen(
                source,
                timeout=self._command_timeout_seconds,
                phrase_time_limit=self._command_timeout_seconds,
            )
        return AudioPacket(
            audio_data=audio_data,
            raw_data=_audio_raw_data(audio_data, self._sample_rate),
            sample_rate=self._sample_rate,
            sample_width=2,
        )


class STTProvider(Protocol):
    name: str
    requires_audio: bool

    def transcribe(self, audio: AudioPacket) -> STTResult:
        ...

    def set_language(self, language: str) -> None:
        ...


class InjectedSTTProvider:
    """Test/dev STT provider backed by a simple transcript function."""

    def __init__(
        self,
        name: str,
        listen_func: ListenFunc,
        *,
        language: str = "en",
    ) -> None:
        self.name = name
        self.requires_audio = False
        self._listen_func = listen_func
        self._language = language

    def transcribe(self, _audio: AudioPacket) -> STTResult:
        started = time.monotonic()
        text = self._listen_func().strip()
        return STTResult(
            text=text,
            language=self._language,
            confidence=0.9 if text else 0.0,
            provider=self.name,
            latency_ms=_elapsed_ms(started),
        )

    def set_language(self, language: str) -> None:
        self._language = "ar-EG" if language == "ar" else "en-US"


class GoogleWebSTTProvider:
    name = "google_web"
    requires_audio = True

    def __init__(self, recognizer: Any, *, language: str = "en-US") -> None:
        self._recognizer = recognizer
        self._language = language

    def transcribe(self, audio: AudioPacket) -> STTResult:
        if audio.audio_data is None:
            raise RuntimeError("Google STT requires SpeechRecognition audio data.")
        started = time.monotonic()
        text = str(
            self._recognizer.recognize_google(
                audio.audio_data,
                language=self._language,
            )
        ).strip()
        return STTResult(
            text=text,
            language=self._language,
            confidence=0.9 if text else 0.0,
            provider=self.name,
            latency_ms=_elapsed_ms(started),
        )

    def set_language(self, language: str) -> None:
        self._language = "ar-EG" if language == "ar" else "en-US"


class VoskAudioSTTProvider:
    name = "vosk"
    requires_audio = True

    def __init__(self, model_path: str | None) -> None:
        self._model_path = model_path or ""
        self._language = "offline"
        self._model: Any | None = None

    def transcribe(self, audio: AudioPacket) -> STTResult:
        if not self._model_path or not Path(self._model_path).exists():
            raise RuntimeError("No Vosk model found.")
        try:
            import vosk
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Vosk is not installed.") from exc

        started = time.monotonic()
        if self._model is None:
            self._model = vosk.Model(str(self._model_path))
        recognizer = vosk.KaldiRecognizer(self._model, audio.sample_rate)
        recognizer.AcceptWaveform(audio.raw_data)
        payload = json.loads(recognizer.FinalResult() or "{}")
        text = str(payload.get("text", "")).strip()
        return STTResult(
            text=text,
            language=self._language,
            confidence=float(payload.get("confidence", 0.75 if text else 0.0)),
            provider=self.name,
            latency_ms=_elapsed_ms(started),
        )

    def set_language(self, language: str) -> None:
        self._language = language
        model_env = "VOSK_MODEL_AR" if language == "ar" else "VOSK_MODEL_EN"
        model_path = os.getenv(model_env, "").strip()
        if model_path and Path(model_path).exists() and model_path != self._model_path:
            self._model_path = model_path
            self._model = None


class DirectVoskSTTProvider:
    """Local Vosk microphone listener using sounddevice."""

    name = "vosk"
    requires_audio = False

    def __init__(
        self,
        model_path: str | None,
        *,
        timeout_seconds: float,
        microphone_index: int | None = None,
        empty_audio_only: bool = False,
    ) -> None:
        self._model_path = model_path or ""
        self._timeout_seconds = timeout_seconds
        self._microphone_index = microphone_index
        self._empty_audio_only = empty_audio_only

    def transcribe(self, audio: AudioPacket) -> STTResult:
        if self._empty_audio_only and not audio.is_empty:
            return STTResult("", "offline", 0.0, self.name, 0)
        if not self._model_path or not Path(self._model_path).exists():
            raise RuntimeError("No Vosk model found.")
        from modules.voice.live_vosk_listener import LiveVoskCommandListener

        started = time.monotonic()
        with LiveVoskCommandListener(
            model_path=self._model_path,
            phrase_timeout_seconds=self._timeout_seconds,
            device_index=self._microphone_index,
        ) as listener:
            text = listener.listen_once().strip()
        return STTResult(
            text=text,
            language="offline",
            confidence=0.75 if text else 0.0,
            provider=self.name,
            latency_ms=_elapsed_ms(started),
        )

    def set_language(self, language: str) -> None:
        model_env = "VOSK_MODEL_AR" if language == "ar" else "VOSK_MODEL_EN"
        model_path = os.getenv(model_env, "").strip()
        if model_path and Path(model_path).exists():
            self._model_path = model_path


class RuntimeSTTService:
    """Provider cascade: online Google first, then Vosk local."""

    def __init__(self, providers: list[STTProvider], *, log_event: Callable[..., None] | None = None) -> None:
        self._providers = providers
        self._log_event = log_event

    @property
    def provider_names(self) -> list[str]:
        return [provider.name for provider in self._providers]

    def transcribe(self, audio: AudioPacket) -> STTResult:
        for index, provider in enumerate(self._providers):
            if audio.is_empty and getattr(provider, "requires_audio", True):
                self._log("STT_PROVIDER_SKIPPED", provider=provider.name, reason="empty_audio")
                continue
            self._log("STT_PROVIDER_START", provider=provider.name, fallback_index=index)
            try:
                result = provider.transcribe(audio)
            except Exception as exc:
                self._log(
                    "STT_PROVIDER_FAILURE",
                    provider=provider.name,
                    fallback_index=index,
                    error=type(exc).__name__,
                    level="WARNING",
                )
                continue
            if result.text.strip():
                self._log(
                    "STT_PROVIDER_SUCCESS",
                    provider=result.provider,
                    latency_ms=result.latency_ms,
                    confidence=result.confidence,
                )
                return result
            self._log(
                "STT_PROVIDER_EMPTY",
                provider=result.provider,
                fallback_index=index,
                latency_ms=result.latency_ms,
            )
        return STTResult("", "", 0.0, "none", 0)

    def set_language(self, language: str) -> None:
        for provider in self._providers:
            setter = getattr(provider, "set_language", None)
            if callable(setter):
                setter(language)

    def _log(self, event: str, /, **fields: Any) -> None:
        if self._log_event is None:
            return
        try:
            self._log_event(event, **fields)
        except Exception:
            pass


class RuntimeVoiceListener:
    """Audio capture + STT provider fallback + command parsing."""

    def __init__(
        self,
        *,
        audio_input: AudioInput,
        stt_service: RuntimeSTTService,
        parser: CommandParser,
        command_timeout_seconds: float,
        language: str = "en",
        log_event: Callable[..., None] | None = None,
    ) -> None:
        self._audio_input = audio_input
        self._stt_service = stt_service
        self._parser = parser
        self._command_timeout_seconds = command_timeout_seconds
        self._language = language
        self._log_event = log_event

    @property
    def provider_names(self) -> list[str]:
        return self._stt_service.provider_names

    def listen_for_command(self) -> ListenerResult:
        self._log("VOICE_LISTEN_START", providers="->".join(self.provider_names))
        stt_result = self._listen_once()
        if not stt_result.text.strip():
            self._log("VOICE_LISTEN_RETRY_EMPTY_STT", provider=stt_result.provider)
            stt_result = self._listen_once()
        parsed = self._parser.parse_text(stt_result.text, language_hint=self._language)
        normalized = self._parser_normalize(stt_result.text)
        self._log(
            "VOICE_COMMAND_PARSED",
            source="voice",
            command=stt_result.text,
            success=parsed.success,
            intent=parsed.intent,
            confidence=parsed.confidence,
            provider=stt_result.provider,
            latency_ms=stt_result.latency_ms,
        )
        return ListenerResult.from_command_result(
            parsed,
            stt_result,
            normalized_text=normalized,
        )

    def set_language(self, language: str) -> None:
        self._language = language
        self._stt_service.set_language(language)

    def shutdown(self) -> None:
        return

    def _listen_once(self) -> STTResult:
        try:
            audio = self._audio_input.listen()
        except Exception as exc:
            sr_module = _sr_module()
            if sr_module is not None and isinstance(exc, sr_module.WaitTimeoutError):
                self._log("AUDIO_TIMEOUT", timeout_seconds=self._command_timeout_seconds)
                return self._stt_service.transcribe(AudioPacket(None, b"", 16000, 2))
            self._log("AUDIO_CAPTURE_FAILURE", error=type(exc).__name__, level="WARNING")
            return self._stt_service.transcribe(AudioPacket(None, b"", 16000, 2))
        if audio.is_empty:
            self._log("AUDIO_CAPTURE_EMPTY")
            return self._stt_service.transcribe(audio)
        self._log(
            "AUDIO_CAPTURED",
            bytes=len(audio.raw_data),
            sample_rate=audio.sample_rate,
            sample_width=audio.sample_width,
        )
        return self._stt_service.transcribe(audio)

    def _log(self, event: str, /, **fields: Any) -> None:
        if self._log_event is None:
            return
        try:
            self._log_event(event, **fields)
        except Exception:
            pass

    @staticmethod
    def _parser_normalize(text: str) -> str:
        from modules.voice.command_parser import normalize_command_phrase

        return normalize_command_phrase(text)


class VoiceRuntimeManager:
    """Always-on command session with provider cascade and no-barge-in."""

    def __init__(
        self,
        *,
        dispatch_command: Callable[[str], object],
        request_shutdown: Callable[[], None],
        voice_enabled: bool,
        voice_model: str | None,
        command_timeout_seconds: float,
        microphone_index: int | None = None,
        stt_provider: str = "auto",
        online_listen_func: ListenFunc | None = None,
        local_listen_func: ListenFunc | None = None,
        parser: CommandParser | None = None,
        speak_func: SpeakFunc | None = None,
        no_barge_in: bool = True,
        confirm_exit: bool = True,
        tts_echo_ignore_seconds: float = 3.0,
        log_event: Callable[..., None] | None = None,
    ) -> None:
        self._dispatch_command = dispatch_command
        self._request_shutdown = request_shutdown
        self._voice_enabled = voice_enabled
        self._voice_model = voice_model
        self._command_timeout_seconds = command_timeout_seconds
        self._microphone_index = microphone_index
        self._stt_provider = stt_provider
        self._online_listen_func = online_listen_func
        self._local_listen_func = local_listen_func
        self._parser = parser or CommandParser()
        self._speak_func = speak_func
        self._no_barge_in = no_barge_in
        self._confirm_exit = confirm_exit
        self._tts_echo_ignore_seconds = max(0.0, tts_echo_ignore_seconds)
        self._log_event = log_event
        self._running = threading.Event()
        self._tts_busy = threading.Event()
        self._state_lock = threading.Lock()
        self._state = VoiceState.IDLE
        self._thread: threading.Thread | None = None
        self._listener: RuntimeVoiceListener | None = None
        self.status = VoiceProviderStatus()
        self.mode = "stopped"
        self.last_status = self.status.message
        self._last_unclear_report = 0.0
        self._last_unclear_text = ""
        self._last_empty_report = 0.0
        self._tts_ignore_until = 0.0
        self._exit_confirmation_pending = False
        self._language = "en"
        self._log(
            "VOICE_MANAGER_INIT",
            stt_provider=stt_provider,
            voice_enabled=voice_enabled,
            no_barge_in=no_barge_in,
            microphone_index=microphone_index,
        )

    @property
    def state(self) -> VoiceState:
        with self._state_lock:
            return self._state

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        normalized = (language or "").strip().lower()
        if normalized in {"ar", "arabic"}:
            self._language = "ar"
            arabic_model = os.getenv("VOSK_MODEL_AR", "").strip()
            if arabic_model and Path(arabic_model).exists():
                self._voice_model = arabic_model
        elif normalized in {"en", "english"}:
            self._language = "en"
            english_model = os.getenv("VOSK_MODEL_EN", "").strip()
            if english_model and Path(english_model).exists():
                self._voice_model = english_model
        if self._listener is not None:
            self._listener.set_language(self._language)
        self._log("VOICE_LANGUAGE_SET", language=self._language, model=self._voice_model)

    def set_tts_busy(self, busy: bool) -> None:
        """Called by the runtime TTS bridge to enforce no-barge-in."""
        if busy:
            self._tts_busy.set()
            self._set_state(VoiceState.SPEAKING)
            self._set_status("voice", self.status.provider, "Speaking; microphone paused.")
            self._log("VOICE_TTS_BUSY_SET", busy=True)
            return
        self._tts_busy.clear()
        self._tts_ignore_until = time.monotonic() + self._tts_echo_ignore_seconds
        self._log("VOICE_TTS_BUSY_SET", busy=False)
        if self._running.is_set():
            self._set_state(VoiceState.ACTIVE_SESSION)

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._thread = threading.Thread(
            target=self._run,
            name="assistant-voice-session",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._set_state(VoiceState.SHUTDOWN)
        self._running.clear()
        listener = self._listener
        if listener is not None:
            listener.shutdown()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _run(self) -> None:
        if not self._voice_enabled:
            self._log("VOICE_FALLBACK_TEXT", reason="voice_disabled")
            self._text_loop("Voice disabled; text fallback active.")
            return
        try:
            self._listener = self._build_listener()
        except Exception as exc:
            self._log(
                "VOICE_LISTENER_INIT_FAILED",
                error=type(exc).__name__,
                error_message=str(exc),
                level="WARNING",
            )
            self._text_loop("Speech recognition unavailable; text fallback active.")
            return
        providers = " -> ".join(self._listener.provider_names) or "none"
        self._log("VOICE_PROVIDER_SELECTED", provider=providers)
        self._set_status("voice", providers, f"{providers} STT listening.")
        print(f"Voice command session started with {providers} STT.")
        self._command_loop()

    def _build_listener(self) -> RuntimeVoiceListener:
        audio_input = _NullAudioInput()
        providers: list[STTProvider] = []
        stt_choice = (self._stt_provider or "auto").strip().lower()
        self._log_microphone_selection()
        if self._online_listen_func is not None:
            providers.append(InjectedSTTProvider("online", self._online_listen_func))
        elif stt_choice in {"auto", "online", "google", "google_web"}:
            try:
                audio_input = AudioInput(
                    command_timeout_seconds=self._command_timeout_seconds,
                    microphone_index=self._microphone_index,
                )
            except Exception as exc:
                self._log(
                    "VOICE_ONLINE_STT_UNAVAILABLE",
                    provider="google_web",
                    error=type(exc).__name__,
                    error_message=str(exc),
                    level="WARNING",
                )
                if stt_choice in {"online", "google", "google_web"}:
                    raise
            else:
                providers.append(GoogleWebSTTProvider(audio_input.recognizer))
        if self._local_listen_func is not None:
            providers.append(InjectedSTTProvider("local", self._local_listen_func))
        elif stt_choice in {"auto", "local", "vosk"} and self._local_available():
            if (
                stt_choice == "auto"
                and not isinstance(audio_input, _NullAudioInput)
                and any(provider.name == "google_web" for provider in providers)
            ):
                providers.append(VoskAudioSTTProvider(self._voice_model))
                providers.append(
                    DirectVoskSTTProvider(
                        self._voice_model,
                        timeout_seconds=self._command_timeout_seconds,
                        microphone_index=self._microphone_index,
                        empty_audio_only=True,
                    )
                )
            else:
                providers.append(
                    DirectVoskSTTProvider(
                        self._voice_model,
                        timeout_seconds=self._command_timeout_seconds,
                        microphone_index=self._microphone_index,
                    )
                )
        if stt_choice in {"local", "vosk"}:
            providers = [provider for provider in providers if provider.name in {"local", "vosk"}]
        elif stt_choice in {"online", "google", "google_web"}:
            providers = [provider for provider in providers if provider.name in {"online", "google_web"}]
        if not providers:
            raise RuntimeError("No STT providers are available.")
        service = RuntimeSTTService(providers, log_event=self._log)
        service.set_language(self._language)
        return RuntimeVoiceListener(
            audio_input=audio_input,
            stt_service=service,
            parser=self._parser,
            command_timeout_seconds=self._command_timeout_seconds,
            language=self._language,
            log_event=self._log,
        )

    def _command_loop(self) -> None:
        assert self._listener is not None
        self._log("VOICE_LISTEN_LOOP_START", provider="->".join(self._listener.provider_names))
        while self._running.is_set():
            if self._no_barge_in and self._tts_busy.is_set():
                self._log("VOICE_WAIT_TTS_BUSY", level="DEBUG")
                time.sleep(0.05)
                continue

            self._set_state(VoiceState.LISTENING)
            result = self._listener.listen_for_command()
            if self._should_ignore_listener_result(result):
                self._log(
                    "VOICE_COMMAND_IGNORED_DURING_TTS",
                    provider=result.stt_provider,
                    latency_ms=result.stt_latency_ms,
                )
                continue
            self._set_state(VoiceState.PROCESSING)
            self._log(
                "VOICE_COMMAND_RESULT",
                intent=result.intent,
                raw_text=result.raw_text,
                normalized=result.normalized_text,
                confidence=result.confidence,
                provider=result.stt_provider,
                latency_ms=result.stt_latency_ms,
                success=result.success,
            )
            if not result.raw_text.strip():
                self._handle_empty_result(result)
                continue
            if not result.success:
                self._handle_unparsed_result(result)
                continue
            self._set_state(VoiceState.EXECUTING)
            self._execute(result)
            self._set_state(VoiceState.ACTIVE_SESSION)

    def _execute(self, result: ListenerResult) -> None:
        if self._should_ignore_listener_result(result):
            self._log(
                "VOICE_COMMAND_IGNORED_DURING_TTS",
                provider=result.stt_provider,
                latency_ms=result.stt_latency_ms,
            )
            return
        if result.intent == CommandIntent.EXIT:
            if self._should_confirm_exit():
                self._handle_exit_confirmation()
                return
            self._log("VOICE_EXIT_COMMAND", source="voice")
            self._request_shutdown()
            return
        self._set_status("voice", self.status.provider, f"Heard: {result.normalized_text}")
        self._dispatch_command(result.raw_text)

    def _should_ignore_listener_result(self, result: ListenerResult) -> bool:
        if not self._no_barge_in:
            return False
        if self._tts_busy.is_set():
            return True
        if time.monotonic() < self._tts_ignore_until:
            return bool(result.raw_text.strip())
        return False

    def _handle_empty_result(self, result: ListenerResult) -> None:
        now = time.monotonic()
        self._set_status("voice", self.status.provider, "No command heard yet.")
        if now - self._last_empty_report < max(18.0, self._command_timeout_seconds * 2.5):
            return
        self._last_empty_report = now
        print("No command heard yet. Say read text clearly.")
        self._log("VOICE_STT_EMPTY", provider=result.stt_provider)

    def _handle_unparsed_result(self, result: ListenerResult) -> None:
        now = time.monotonic()
        normalized = " ".join(result.normalized_text.split())
        self._set_status("voice", self.status.provider, "Unclear audio; waiting.")
        self._log(
            "VOICE_UNPARSED",
            provider=result.stt_provider,
            confidence=result.confidence,
            guidance=result.guidance,
        )
        if normalized == self._last_unclear_text and now - self._last_unclear_report < 12.0:
            return
        if now - self._last_unclear_report < 8.0:
            return
        self._last_unclear_text = normalized
        self._last_unclear_report = now
        print("Heard audio, but not a supported command. Try: read text.")
        self._log("VOICE_COMMAND_UNCLEAR", provider=result.stt_provider)

    def _text_loop(self, message: str) -> None:
        self._set_status("text", "keyboard", message)
        self._set_state(VoiceState.ACTIVE_SESSION)
        print(f"{message} Type help for commands.")
        self._log("TEXT_COMMAND_LOOP_START", message=message)
        while self._running.is_set():
            try:
                command = input("assistant> ").strip()
            except (EOFError, KeyboardInterrupt):
                self._request_shutdown()
                return
            if command:
                self._handle_command(command, source="text")

    def _listen_online_once(self) -> str:
        audio_input = AudioInput(
            command_timeout_seconds=self._command_timeout_seconds,
            microphone_index=self._microphone_index,
        )
        provider = GoogleWebSTTProvider(audio_input.recognizer)
        provider.set_language(self._language)
        audio = audio_input.listen()
        return provider.transcribe(audio).text.strip().lower()

    def _listen_local_once(self) -> str:
        if self._local_listen_func is not None:
            return self._local_listen_func()
        from modules.voice.live_vosk_listener import LiveVoskCommandListener

        with LiveVoskCommandListener(
            model_path=self._voice_model or "",
            phrase_timeout_seconds=self._command_timeout_seconds,
            device_index=self._microphone_index,
        ) as listener:
            return listener.listen_once()

    def _handle_command(self, command: str, *, source: str) -> None:
        normalized_command = command.strip()
        if not normalized_command:
            return
        parsed = self._parser.parse_text(normalized_command, language_hint=self._language)
        self._log(
            "VOICE_COMMAND_PARSED",
            source=source,
            command=normalized_command,
            success=parsed.success,
            intent=parsed.intent,
            confidence=parsed.confidence,
        )
        if parsed.success and parsed.intent == CommandIntent.EXIT:
            if self._should_confirm_exit():
                self._handle_exit_confirmation()
                return
            self._log("VOICE_EXIT_COMMAND", source=source)
            self._request_shutdown()
            return
        if source == "voice" and not parsed.success:
            result = ListenerResult(
                intent=None,
                raw_text=normalized_command,
                normalized_text=RuntimeVoiceListener._parser_normalize(normalized_command),
                success=False,
                confidence=parsed.confidence,
                stt_provider=self.status.provider,
                guidance=parsed.guidance,
            )
            self._handle_unparsed_result(result)
            return
        self._set_status(source, self.status.provider, f"Heard: {normalized_command}")
        self._dispatch_command(normalized_command)

    def _local_available(self) -> bool:
        if self._local_listen_func is not None:
            return True
        return bool(self._voice_model and Path(self._voice_model).exists())

    def _should_confirm_exit(self) -> bool:
        if not self._confirm_exit:
            return False
        if self._exit_confirmation_pending:
            self._exit_confirmation_pending = False
            return False
        self._exit_confirmation_pending = True
        return True

    def _handle_exit_confirmation(self) -> None:
        guidance = (
            "قول خروج تاني للتأكيد."
            if self._language == "ar"
            else "Say exit again to confirm."
        )
        self._set_status("voice", self.status.provider, guidance)
        if self._speak_func is not None:
            self._speak_func(guidance, self._language if self._language in {"ar", "en"} else "en")
        else:
            print(guidance)
        self._log("VOICE_EXIT_CONFIRMATION_REQUESTED")

    def _log_microphone_selection(self) -> None:
        names = _microphone_names()
        selected = self._microphone_index
        if selected is None:
            selected_name = "system_default"
        elif 0 <= selected < len(names):
            selected_name = names[selected]
        else:
            selected_name = "invalid_index"
        self._log(
            "VOICE_MICROPHONE_SELECTED",
            microphone_index=selected if selected is not None else "default",
            microphone_name=selected_name,
            microphone_count=len(names),
        )
        if selected_name == "invalid_index":
            print(
                f"Microphone warning: ASSISTANT_MICROPHONE_INDEX={selected} "
                "is not in the available device list."
            )

    def _set_state(self, state: VoiceState) -> None:
        with self._state_lock:
            if self._state != state:
                self._log("VOICE_STATE", previous=self._state, current=state)
            self._state = state
        if state == VoiceState.SPEAKING:
            self.mode = "speaking"
        elif state in {VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.EXECUTING}:
            self.mode = "voice"
        elif state == VoiceState.SHUTDOWN:
            self.mode = "stopped"

    def _set_status(self, mode: str, provider: str, message: str) -> None:
        self.mode = mode
        self.status = VoiceProviderStatus(mode=mode, provider=provider, message=message)
        self.last_status = message

    def _log(self, event: str, /, **fields: Any) -> None:
        if self._log_event is None:
            return
        try:
            self._log_event(event, **fields)
        except Exception:
            pass


class _NullAudioInput:
    """Audio input placeholder for injected STT tests."""

    def listen(self) -> AudioPacket:
        return AudioPacket(audio_data=None, raw_data=b"injected", sample_rate=16000, sample_width=2)


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _sr_module() -> Any | None:
    """Return the current SpeechRecognition module, honoring test monkeypatches."""
    return sys.modules.get("speech_recognition", sr)


def _microphone_names() -> list[str]:
    sr_module = _sr_module()
    if sr_module is not None:
        microphone = getattr(sr_module, "Microphone", None)
        lister = getattr(microphone, "list_microphone_names", None)
        if callable(lister):
            try:
                names = [str(name) for name in lister()]
            except Exception:
                names = []
            if names:
                return names
    try:
        import sounddevice as sd

        return [str(device.get("name", "")) for device in sd.query_devices()]
    except Exception:
        return []


def _audio_raw_data(audio_data: Any, sample_rate: int) -> bytes:
    getter = getattr(audio_data, "get_raw_data", None)
    if callable(getter):
        return getter(convert_rate=sample_rate, convert_width=2)
    return b"injected"


__all__ = [
    "AudioInput",
    "AudioPacket",
    "ListenerResult",
    "RuntimeSTTService",
    "RuntimeVoiceListener",
    "STTResult",
    "VoiceProviderStatus",
    "VoiceRuntimeManager",
    "VoiceState",
]
