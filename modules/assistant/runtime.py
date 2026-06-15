"""Integrated always-on runtime for the Blind OCR Assistant."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import importlib
import os
from pathlib import Path
import queue
import threading
import time
from typing import Any

from config import AppConfig, load_config
from modules.assistant.audio_cues import AudioCueManager
from modules.assistant.capture_gate import CaptureGate
from modules.assistant.frame_analyzer import FrameAnalyzer
from modules.assistant.job_worker import JobWorker
from modules.assistant.runtime_controller import RuntimeController, RuntimeControllerMode
from modules.assistant.runtime_state import (
    FrameReadiness,
    RuntimeStateSnapshot,
    RuntimeSystemMode,
)
from modules.assistant.workflow import AssistantWorkflow
from modules.camera.camera_models import (
    BestFrameSelectionResult,
    CameraError,
    CameraErrorCode,
    CameraSourceType,
    CaptureBurstResult,
    CleanupStatus,
    FrameCandidate,
)
from modules.camera.frame_selector import select_best_frame
from modules.common.bootstrap import run_self_check
from modules.common.logging import log_kv_event, setup_logging
from modules.deployment.diagnostics import (
    format_report_for_cli,
    run_lightweight_startup_diagnostics,
)
from modules.deployment.readiness_checks import offline_recovery_spoken_summary
from modules.deployment.readiness_models import ReadinessStatus
from modules.image_processing.image_models import ImageInput
from modules.image_processing.quality_checker import assess_image_quality
from modules.voice.command_parser import CommandParser
from modules.voice.command_models import CommandIntent
from modules.voice.voice_runtime_manager import VoiceRuntimeManager
from modules.voice.voice_models import SpeechOperation, SpeechRequest


class RuntimeMode(str, Enum):
    """High-level runtime lifecycle state."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    SEARCHING_TEXT = "SEARCHING_TEXT"
    READY_TO_CAPTURE = "READY_TO_CAPTURE"
    CAPTURING = "CAPTURING"
    GUIDING = "GUIDING"
    ANALYZING = "ANALYZING"
    OCR = "OCR"
    OCR_ONLINE = "OCR_ONLINE"
    OCR_LOCAL = "OCR_LOCAL"
    READING = "READING"
    TRANSLATING = "TRANSLATING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"


@dataclass(frozen=True)
class AssistantRuntimeOptions:
    """Runtime defaults for laptop-first integrated operation."""

    camera_source: str = ""
    camera_index: int = 0
    voice_enabled: bool = True
    microphone_index: int | None = None
    runtime_mode: str = "laptop"
    command_timeout_seconds: float = 8.0
    tts_engine: str = "auto"
    startup_checks_enabled: bool = True
    high_accuracy: bool = False
    offline: bool = False
    frame_interval_seconds: float = 1.0 / 15.0
    voice_model: str | None = None
    show_window: bool = True
    allow_uncertain_frame: bool = False
    default_language: str = "auto"
    audio_cues_enabled: bool = True
    guided_capture_enabled: bool = True
    guided_capture_timeout_seconds: float = 8.0
    tts_provider: str = "auto"
    stt_provider: str = "auto"
    edge_tts_ar_voice: str = "ar-EG-SalmaNeural"
    edge_tts_en_voice: str = "en-US-JennyNeural"
    frame_analysis_interval_seconds: float = 0.35
    stable_text_frames: int = 3
    text_confidence_threshold: float = 0.55
    guidance_cooldown_seconds: float = 3.0
    capture_override_enabled: bool = True
    quiet_mode: bool = False
    voice_reply_style: str = "normal"
    welcome_language: str = "auto"
    command_confirm_exit: bool = True
    terminal_logs_enabled: bool = True
    welcome_text: str = (
        "Blind OCR assistant is running. Say read text, or type a command."
    )

    @classmethod
    def from_config(cls, config: AppConfig) -> "AssistantRuntimeOptions":
        return cls(
            camera_source=config.assistant_camera_source,
            camera_index=config.assistant_camera_index,
            voice_enabled=config.assistant_voice_enabled,
            microphone_index=config.assistant_microphone_index,
            runtime_mode=config.assistant_runtime_mode,
            command_timeout_seconds=config.assistant_command_timeout_seconds,
            voice_model=_resolve_vosk_model_path(None),
            show_window=config.assistant_show_window,
            default_language=config.assistant_default_language,
            audio_cues_enabled=config.assistant_audio_cues_enabled,
            guided_capture_enabled=config.assistant_guided_capture_enabled,
            guided_capture_timeout_seconds=config.assistant_guided_capture_timeout_seconds,
            tts_provider=config.assistant_tts_provider,
            stt_provider=config.assistant_stt_provider,
            edge_tts_ar_voice=config.assistant_edge_tts_ar_voice,
            edge_tts_en_voice=config.assistant_edge_tts_en_voice,
            frame_analysis_interval_seconds=config.assistant_frame_analysis_interval_seconds,
            stable_text_frames=config.assistant_stable_text_frames,
            text_confidence_threshold=config.assistant_text_confidence_threshold,
            guidance_cooldown_seconds=config.assistant_guidance_cooldown_seconds,
            capture_override_enabled=config.assistant_capture_override_enabled,
            quiet_mode=config.assistant_quiet_mode,
            voice_reply_style=config.assistant_voice_reply_style,
            welcome_language=config.assistant_welcome_language,
            command_confirm_exit=config.assistant_command_confirm_exit,
            terminal_logs_enabled=config.assistant_terminal_logs_enabled,
        )


class RuntimeCommandSession:
    """Voice-first command session with text fallback."""

    def __init__(
        self,
        *,
        dispatch_command: Callable[[str], object],
        request_shutdown: Callable[[], None],
        voice_enabled: bool,
        voice_model: str | None,
        command_timeout_seconds: float,
    ) -> None:
        self._dispatch_command = dispatch_command
        self._request_shutdown = request_shutdown
        self._voice_enabled = voice_enabled
        self._voice_model = voice_model
        self._command_timeout_seconds = command_timeout_seconds
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._listener: Any | None = None
        self.mode = "stopped"
        self.last_status = "Command session is stopped."
        self._parser = CommandParser()
        self._last_unclear_report = 0.0
        self._last_unclear_text = ""

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        target = self._voice_loop if self._can_use_voice() else self._text_loop
        self._thread = threading.Thread(
            target=target,
            name="assistant-command-session",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        listener = self._listener
        if listener is not None:
            try:
                listener.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _can_use_voice(self) -> bool:
        if not self._voice_enabled:
            self.mode = "text"
            self.last_status = "Voice disabled; text fallback active."
            print("Voice input disabled. Text command fallback is active.")
            return False
        model_path = Path(self._voice_model or _resolve_vosk_model_path(None))
        if not model_path.exists():
            self.mode = "text"
            self.last_status = "Voice model missing; text fallback active."
            print(f"Voice model not found at {model_path}. Text command fallback is active.")
            return False
        self._voice_model = str(model_path)
        self.mode = "voice"
        self.last_status = "Voice command session is ready."
        return True

    def _voice_loop(self) -> None:
        from modules.voice.live_vosk_listener import LiveVoskCommandListener

        try:
            self._listener = LiveVoskCommandListener(
                model_path=self._voice_model or _resolve_vosk_model_path(None),
                phrase_timeout_seconds=self._command_timeout_seconds,
            )
            with self._listener:
                print("Voice command session started.")
                last_empty_report = 0.0
                while self._running.is_set():
                    self.last_status = "Listening for a command..."
                    command = self._listener.listen_once().strip()
                    if command:
                        self.last_status = f"Heard: {command}"
                        self._handle_command(command, source="voice")
                    elif time.monotonic() - last_empty_report >= max(
                        12.0,
                        self._command_timeout_seconds * 2,
                    ):
                        last_empty_report = time.monotonic()
                        self.last_status = "No command heard yet."
                        print("No command heard yet. Say read text clearly.")
        except Exception as exc:
            print(f"Voice input failed: {type(exc).__name__}: {exc}")
            print("Text command fallback is active.")
            self.mode = "text"
            self.last_status = "Voice failed; text fallback active."
            self._text_loop()

    def _text_loop(self) -> None:
        print("Text command session started. Type help for commands.")
        self.last_status = "Text command fallback is active."
        while self._running.is_set():
            try:
                command = input("assistant> ").strip()
            except EOFError:
                self._request_shutdown()
                return
            except KeyboardInterrupt:
                self._request_shutdown()
                return
            if command:
                self.last_status = f"Typed: {command}"
                self._handle_command(command, source="text")

    def _handle_command(self, command: str, *, source: str = "text") -> None:
        if _is_runtime_exit_command(command):
            self._request_shutdown()
            return
        if source == "voice" and not self._is_supported_voice_command(command):
            self._handle_unclear_voice_command(command)
            return
        self._dispatch_command(command)

    def _is_supported_voice_command(self, command: str) -> bool:
        return bool(self._parser.parse_text(command).success)

    def _handle_unclear_voice_command(self, command: str) -> None:
        now = time.monotonic()
        normalized = " ".join(command.lower().split())
        self.last_status = "Heard unclear audio; waiting for a supported command."
        if normalized == self._last_unclear_text and now - self._last_unclear_report < 10.0:
            return
        if now - self._last_unclear_report < 6.0:
            return
        self._last_unclear_text = normalized
        self._last_unclear_report = now
        print("Heard audio, but not a supported command. Try: read text.")


class AssistantRuntime:
    """Main integration orchestrator for camera, voice, OCR, TTS, and translation."""

    def __init__(
        self,
        *,
        config: AppConfig | None = None,
        options: AssistantRuntimeOptions | None = None,
        camera_source: Any | None = None,
        workflow: AssistantWorkflow | None = None,
        command_session_factory: Callable[..., RuntimeCommandSession] | None = None,
        startup_check: Callable[[], int] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or load_config()
        self.options = options or AssistantRuntimeOptions.from_config(self.config)
        self._camera_source = camera_source or self._build_camera_source()
        self._workflow = workflow
        self._command_session_factory = command_session_factory or VoiceRuntimeManager
        self._startup_check = startup_check or self._run_startup_checks
        self._sleep = sleep
        self._state = RuntimeMode.IDLE
        self._shutdown_requested = threading.Event()
        self._latest_frame: Any | None = None
        self._latest_frame_timestamp = 0.0
        self._recent_frames: list[tuple[float, Any]] = []
        self._latest_frame_lock = threading.Lock()
        self._command_queue: queue.Queue[str] = queue.Queue()
        self._command_session: RuntimeCommandSession | None = None
        self._controller: RuntimeController | None = None
        self._audio_cues = AudioCueManager(enabled=self.options.audio_cues_enabled)
        self._job_worker = JobWorker()
        self._frame_analyzer = FrameAnalyzer(
            stable_required_frames=self.options.stable_text_frames,
            text_confidence_threshold=self.options.text_confidence_threshold,
        )
        self._capture_gate = CaptureGate(
            capture_override_enabled=self.options.capture_override_enabled
        )
        self._snapshot = RuntimeStateSnapshot(quiet_mode=self.options.quiet_mode)
        self._snapshot_lock = threading.Lock()
        self._modules: dict[str, object] | None = None
        self._latest_guidance = ""
        self._latest_command = ""
        self._latest_camera_status = "Camera is not open."
        self._latest_quality_status = "Quality not checked yet."
        self._latest_operation = "Starting"
        self._latest_ocr_attempts = "-"
        self._latest_translation_provider = "-"
        self._latest_voice_provider = "starting"
        self._gui_available = True
        self._last_frame_analysis_at = 0.0
        self._last_readiness_log_at = 0.0
        self._last_readiness_log_signature = ""
        self._last_capture_boundary_log_at = 0.0
        self._last_capture_boundary_log_signature = ""
        self._capture_override_active = False
        self._exit_confirmation_pending = False
        self._logger = setup_logging(
            self.config.logs_dir,
            self.config.log_level,
            console=self.options.terminal_logs_enabled,
        )
        self._log(
            "RUNTIME_INIT",
            mode=self.options.runtime_mode,
            camera_index=self.options.camera_index,
            voice_enabled=self.options.voice_enabled,
            stt_provider=self.options.stt_provider,
            tts_provider=self.options.tts_provider,
            show_window=self.options.show_window,
        )

    @property
    def state(self) -> RuntimeMode:
        return self._state

    @property
    def workflow(self) -> AssistantWorkflow:
        if self._workflow is None:
            self._workflow = self._build_workflow()
        return self._workflow

    def run(self) -> int:
        """Start the integrated assistant runtime."""
        if self.options.startup_checks_enabled:
            self._log("STARTUP_CHECKS_START")
            startup_code = self._startup_check()
            self._log("STARTUP_CHECKS_DONE", exit_code=startup_code)
            if startup_code != 0:
                return startup_code

        if not self._open_camera():
            self._state = RuntimeMode.ERROR
            self._log("CAMERA_OPEN_FAILED", camera_index=self.options.camera_index, level="ERROR")
            return 1

        print("Assistant runtime started.")
        print(
            "Commands: read text, capture now, cancel, status, what do you see, "
            "repeat guidance, translate to arabic, translate to english, "
            "stop, continue, repeat sentence, repeat paragraph, quiet mode, "
            "verbose mode, voice test, help, exit"
        )
        self._print_runtime_readiness()
        self._state = RuntimeMode.LISTENING
        self._log("RUNTIME_STARTED", state=self._state)
        self._announce_welcome()
        self._start_command_session()
        try:
            while not self._shutdown_requested.is_set():
                frame = self._capture_latest_frame()
                self._analyze_latest_frame_if_due()
                self._drain_command_queue()
                if frame is not None:
                    self._render_gui(frame)
                self._sleep(self.options.frame_interval_seconds)
        except KeyboardInterrupt:
            self.request_shutdown()
        finally:
            self._shutdown()
        return 0

    def request_shutdown(self) -> None:
        self._log("SHUTDOWN_REQUESTED")
        self._shutdown_requested.set()

    def dispatch_command(self, command: str) -> object:
        """Route one text command through the integrated workflow."""
        normalized = (command or "").strip()
        if not normalized:
            return None
        if _is_runtime_exit_command(normalized):
            if self._should_confirm_exit():
                return self._exit_confirmation_result()
            self.request_shutdown()
            return None
        self._latest_command = normalized

        parser_result = CommandParser().parse_text(normalized)
        self._log(
            "COMMAND_DISPATCH",
            command=normalized,
            parser_success=parser_result.success,
            intent=parser_result.intent,
            confidence=parser_result.confidence,
        )
        if parser_result.success and parser_result.intent == CommandIntent.READ:
            self._state = RuntimeMode.SEARCHING_TEXT
        elif parser_result.success and parser_result.intent in {
            CommandIntent.TRANSLATE_TO_ARABIC,
            CommandIntent.TRANSLATE_TO_ENGLISH,
        }:
            self._state = RuntimeMode.TRANSLATING

        result = self.controller.handle_command(
            normalized,
            high_accuracy=self.options.high_accuracy,
        )
        self._print_result(result)
        self._latest_guidance = str(getattr(result, "guidance", "") or "")
        self._log(
            "COMMAND_RESULT",
            success=getattr(result, "success", None),
            guidance=getattr(result, "guidance", ""),
            result_type=type(result).__name__,
        )
        self._update_snapshot(latest_guidance=self._latest_guidance)
        self._speak_guidance_if_needed(result)
        if (
            not self._shutdown_requested.is_set()
            and self._state not in {RuntimeMode.SEARCHING_TEXT, RuntimeMode.ANALYZING}
        ):
            self._state = RuntimeMode.LISTENING
        return result

    @property
    def controller(self) -> RuntimeController:
        if self._controller is None:
            self._controller = RuntimeController(
                workflow=self.workflow,
                capture_preview=self._latest_frame_capture_boundary,
                speak=lambda text, language: self._speak_text(text, language=language),
                set_mode=self._set_controller_mode,
                start_cue=self._start_audio_cue,
                stop_cue=self._stop_audio_cue,
                job_worker=self._job_worker,
                capture_gate=self._capture_gate,
                set_capture_override=self._set_capture_override,
                on_job_result=self._handle_job_result,
                on_guidance=self._handle_controller_guidance,
                on_language_change=self._handle_language_change,
                log_event=self._log,
                guided_capture_enabled=self.options.guided_capture_enabled,
                guided_capture_timeout_seconds=self.options.guided_capture_timeout_seconds,
                guidance_cooldown_seconds=self.options.guidance_cooldown_seconds,
                quiet_mode=(
                    self.options.quiet_mode
                    or self.options.voice_reply_style == "quiet"
                ),
                verbose_mode=self.options.voice_reply_style == "verbose",
                language=self.options.default_language,
            )
        return self._controller

    def _set_controller_mode(self, mode: RuntimeControllerMode) -> None:
        mapping = {
            RuntimeControllerMode.LISTENING: RuntimeMode.LISTENING,
            RuntimeControllerMode.SEARCHING_TEXT: RuntimeMode.SEARCHING_TEXT,
            RuntimeControllerMode.READY_TO_CAPTURE: RuntimeMode.READY_TO_CAPTURE,
            RuntimeControllerMode.CAPTURING: RuntimeMode.CAPTURING,
            RuntimeControllerMode.ANALYZING: RuntimeMode.ANALYZING,
            RuntimeControllerMode.OCR_ONLINE: RuntimeMode.OCR_ONLINE,
            RuntimeControllerMode.OCR_LOCAL: RuntimeMode.OCR_LOCAL,
            RuntimeControllerMode.TRANSLATING: RuntimeMode.TRANSLATING,
            RuntimeControllerMode.SPEAKING: RuntimeMode.SPEAKING,
            RuntimeControllerMode.ERROR: RuntimeMode.ERROR,
        }
        self._state = mapping.get(mode, RuntimeMode.LISTENING)
        self._latest_operation = mode.value
        self._log("STATE_CHANGE", mode=mode.value, runtime_state=self._state.value)
        self._update_snapshot(mode=_snapshot_mode_for_runtime(self._state))

    def _set_capture_override(self, enabled: bool) -> None:
        self._capture_override_active = enabled
        self._log("CAPTURE_OVERRIDE", enabled=enabled)

    def _handle_controller_guidance(self, guidance: str) -> None:
        self._latest_guidance = guidance
        self._update_snapshot(latest_guidance=guidance)

    def _handle_language_change(self, language: str) -> None:
        session = self._command_session
        setter = getattr(session, "set_language", None)
        if callable(setter):
            setter(language)
        self._latest_voice_provider = f"language:{language}"
        self._log("LANGUAGE_SWITCH", language=language)

    def _handle_job_result(self, result: Any) -> None:
        guidance = str(getattr(result, "guidance", "") or "")
        summary = guidance
        if hasattr(result, "selected_ocr_engine"):
            summary = (
                f"OCR {getattr(result, 'selected_ocr_engine', 'unknown')} "
                f"success={getattr(result, 'success', False)}"
            )
            self._debug_print_text(
                "OCR raw text",
                getattr(result, "raw_text", ""),
            )
            self._debug_print_text(
                "OCR clean text",
                getattr(result, "clean_text", ""),
            )
        elif hasattr(result, "translated_text"):
            summary = f"Translation success={getattr(result, 'success', False)}"
            self._debug_print_text(
                "Translated text",
                getattr(result, "translated_text", ""),
            )
        self._latest_guidance = guidance or self._latest_guidance
        self._update_snapshot(
            latest_guidance=self._latest_guidance,
            latest_result_summary=summary,
            provider_attempts=tuple(
                part.strip()
                for part in str(self._latest_ocr_attempts or "").split("|")
                if part.strip() and part.strip() != "-"
            ),
        )
        self._log(
            "JOB_RESULT",
            result_type=type(result).__name__,
            success=getattr(result, "success", None),
            guidance=getattr(result, "guidance", ""),
            summary=summary,
        )

    def _start_audio_cue(self, label: str) -> None:
        self._latest_operation = f"loading:{label}"
        self._log("AUDIO_CUE_START", label=label)
        self._audio_cues.start(label)

    def _stop_audio_cue(self) -> None:
        if self._audio_cues.active_label:
            self._log("AUDIO_CUE_STOP", label=self._audio_cues.active_label)
        self._audio_cues.stop()

    def _build_camera_source(self) -> Any:
        from modules.camera.orbbec_camera import GenericRGBCameraSource

        if self.options.camera_source:
            return GenericRGBCameraSource(
                camera_source=self.options.camera_source,
                source_id=f"runtime-opencv-rgb-{self.options.camera_source}",
            )
        return GenericRGBCameraSource(
            camera_index=self.options.camera_index,
            source_id=f"runtime-opencv-rgb-{self.options.camera_index}",
        )

    def _open_camera(self) -> bool:
        camera_label = self.options.camera_source or self.options.camera_index
        print(f"Opening camera {camera_label}...")
        self._log("CAMERA_OPEN_START", camera_source=camera_label)
        try:
            opened = bool(self._camera_source.open())
        except Exception as exc:
            print(f"Camera unavailable: {type(exc).__name__}: {exc}")
            return False
        if not opened:
            print("Camera unavailable. Check the laptop camera and try again.")
            return False
        self._log("CAMERA_OPEN_OK", camera_source=camera_label)
        return True

    def _capture_latest_frame(self) -> Any | None:
        try:
            frame = self._camera_source.capture_frame()
        except Exception as exc:
            self._state = RuntimeMode.ERROR
            self._latest_camera_status = f"Frame read failed: {type(exc).__name__}"
            self._log("FRAME_READ_FAILED", error=type(exc).__name__, level="ERROR")
            print(f"Camera frame read failed: {type(exc).__name__}: {exc}")
            self.request_shutdown()
            return None
        with self._latest_frame_lock:
            captured_at = time.monotonic()
            self._latest_frame = frame
            self._latest_frame_timestamp = captured_at
            self._recent_frames.append((captured_at, frame))
            self._recent_frames = [
                item
                for item in self._recent_frames[-12:]
                if captured_at - item[0] <= 3.0
            ]
        self._latest_camera_status = "Camera live."
        return frame

    def _analyze_latest_frame_if_due(self) -> None:
        now = time.monotonic()
        if (
            now - self._last_frame_analysis_at
            < self.options.frame_analysis_interval_seconds
        ):
            return
        self._last_frame_analysis_at = now
        capture = self._latest_frame_capture_boundary()
        readiness = self._frame_analyzer.analyze_capture(capture)
        self._latest_quality_status = readiness.quality_summary
        self._log_readiness_if_needed(readiness)
        self._update_snapshot(
            latest_frame_readiness=readiness,
            latest_guidance=readiness.guidance
            if self._state == RuntimeMode.SEARCHING_TEXT
            else self._latest_guidance,
        )
        self.controller.on_frame_readiness(readiness)

    def _log_readiness_if_needed(self, readiness: FrameReadiness) -> None:
        now = time.monotonic()
        signature = (
            f"{readiness.guidance_code}|{readiness.has_text}|"
            f"{readiness.ready_to_capture}"
        )
        should_log = signature != self._last_readiness_log_signature
        if self._state == RuntimeMode.SEARCHING_TEXT and now - self._last_readiness_log_at >= 2.0:
            should_log = True
        elif self._state != RuntimeMode.SEARCHING_TEXT and now - self._last_readiness_log_at < 8.0:
            should_log = False
        if not should_log:
            return
        self._last_readiness_log_signature = signature
        self._last_readiness_log_at = now
        self._log(
            "FRAME_READINESS",
            mode=self._state,
            has_text=readiness.has_text,
            confidence=readiness.text_confidence,
            stable_frames=readiness.stable_frames,
            ready=readiness.ready_to_capture,
            guidance_code=readiness.guidance_code,
            brightness_ok=readiness.brightness_ok,
            blur_ok=readiness.blur_ok,
            quality=readiness.quality_summary,
        )

    def _update_snapshot(self, **updates: Any) -> None:
        if "mode" not in updates:
            updates["mode"] = _snapshot_mode_for_runtime(self._state)
        active_job = self._job_worker.active_job
        if active_job is not None:
            updates.setdefault("active_job", active_job)
        updates.setdefault("quiet_mode", self.options.quiet_mode)
        with self._snapshot_lock:
            self._snapshot = self._snapshot.with_updates(**updates)

    def _snapshot_copy(self) -> RuntimeStateSnapshot:
        with self._snapshot_lock:
            return self._snapshot

    def _log(self, event: str, /, *, level: str = "INFO", **fields: Any) -> None:
        try:
            if self.config.assistant_voice_transcript_logs_enabled:
                for key in ("command", "phrase", "recognized_phrase"):
                    if key in fields and fields[key] is not None:
                        fields[f"debug_{key}"] = fields[key]
            if self.config.sensitive_text_logging:
                for key in ("raw_text", "clean_text", "translated_text", "ocr_text", "text"):
                    if key in fields and fields[key] is not None:
                        fields[f"debug_{key}"] = fields[key]
            log_kv_event(self._logger, event, level=level, **fields)
        except Exception:
            pass

    def _debug_print_text(self, label: str, text: Any) -> None:
        if not self.config.sensitive_text_logging:
            return
        value = str(text or "").strip()
        if not value:
            print(f"{label}: <empty>")
            return
        snippet = value.replace("\r", " ").replace("\n", " ")
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        print(f"{label}: {snippet}")

    def _start_command_session(self) -> None:
        kwargs = {
            "dispatch_command": self._enqueue_command,
            "request_shutdown": self.request_shutdown,
            "voice_enabled": self.options.voice_enabled,
            "voice_model": self.options.voice_model,
            "microphone_index": self.options.microphone_index,
            "command_timeout_seconds": self.options.command_timeout_seconds,
            "stt_provider": self.options.stt_provider,
            "confirm_exit": self.options.command_confirm_exit,
            "log_event": self._log,
        }
        try:
            self._command_session = self._command_session_factory(**kwargs)
        except TypeError:
            kwargs.pop("log_event", None)
            kwargs.pop("stt_provider", None)
            kwargs.pop("microphone_index", None)
            kwargs.pop("confirm_exit", None)
            self._command_session = self._command_session_factory(**kwargs)
        self._command_session.start()
        self._log(
            "COMMAND_SESSION_STARTED",
            session_type=type(self._command_session).__name__,
            voice_enabled=self.options.voice_enabled,
            stt_provider=self.options.stt_provider,
        )
        if self.options.default_language in {"ar", "en"}:
            setter = getattr(self._command_session, "set_language", None)
            if callable(setter):
                setter(self.options.default_language)

    def _announce_welcome(self) -> None:
        language = self._welcome_language()
        text = (
            "المساعد جاهز. قول اقرأ، ترجم، أو توقف."
            if language == "ar"
            else self.options.welcome_text
        )
        print(text)
        self._latest_guidance = text
        self._speak_text(text, language=language)

    def _welcome_language(self) -> str:
        if self.options.welcome_language in {"ar", "en"}:
            return self.options.welcome_language
        if self.options.default_language in {"ar", "en"}:
            return self.options.default_language
        return "en"

    def _should_confirm_exit(self) -> bool:
        if not self.options.command_confirm_exit:
            return False
        if self._exit_confirmation_pending:
            self._exit_confirmation_pending = False
            return False
        self._exit_confirmation_pending = True
        return True

    def _exit_confirmation_result(self) -> object:
        arabic = self.options.default_language == "ar"
        guidance = "قول خروج تاني للتأكيد." if arabic else "Say exit again to confirm."
        result = type("_ExitConfirmationResult", (), {"success": True, "guidance": guidance})()
        self._latest_guidance = guidance
        self._speak_text(guidance, language="ar" if arabic else "en")
        return result

    def _enqueue_command(self, command: str) -> None:
        self._command_queue.put(command)
        self._log("COMMAND_ENQUEUED", command=command, queue_size=self._command_queue.qsize())

    def _drain_command_queue(self) -> None:
        while not self._command_queue.empty():
            try:
                command = self._command_queue.get_nowait()
            except queue.Empty:
                return
            self.dispatch_command(command)

    def _build_workflow(self) -> AssistantWorkflow:
        modules = self._load_modules()
        reading_controller = modules["reading"].ReadingController(
            _build_tts_engine(
                modules=modules,
                tts_engine=self.options.tts_engine,
                tts_provider=self.options.tts_provider,
                ar_voice=self.options.edge_tts_ar_voice,
                en_voice=self.options.edge_tts_en_voice,
                log_event=self._log,
            )
        )
        reading_controller = _CueAwareReadingController(
            reading_controller,
            before_speak=self._stop_audio_cue,
            set_tts_busy=self._set_voice_tts_busy,
        )
        online_translation = modules["translation_online"].OnlineFallbackTranslationEngine(
            primary=modules["translation_online"].GoogleTranslatorEngine(),
            backup=modules["translation_online"].MyMemoryTranslatorEngine(),
        )
        if (
            self.config.assistant_gemini_translation_enabled
            and self.config.gemini_api_key
            and not self.options.offline
        ):
            online_translation = modules["translation_online"].OnlineFallbackTranslationEngine(
                primary=modules["gemini_translation"].GeminiTranslationEngine(
                    api_key=self.config.gemini_api_key,
                    model=self.config.assistant_gemini_translation_model,
                    timeout_seconds=self.config.assistant_gemini_translation_timeout_seconds,
                ),
                backup=online_translation,
            )
        if self.config.libretranslate_url:
            online_translation = modules["translation_online"].OnlineFallbackTranslationEngine(
                primary=online_translation,
                backup=modules["libre_translate"].LibreTranslateClient(
                    endpoint=self.config.libretranslate_url,
                    api_key=self.config.libretranslate_api_key,
                ),
            )
        translation_controller = modules["translation_controller"].TranslationController(
            online_engine=online_translation,
            offline_engine=modules["translation_argos"].ArgosTranslateFallback(),
            reading_controller=reading_controller,
        )
        return AssistantWorkflow(
            dialogue_manager=modules["dialogue"].DialogueManager(route_immediately=False),
            capture_burst=self._latest_frame_capture_boundary,
            run_ocr_cascade=self._ocr_boundary,
            clean_ocr_text=modules["cleanup"].clean_ocr_text,
            reading_controller=reading_controller,
            translation_controller=translation_controller,
            online_status_provider=lambda: self._online_ocr_allowed(),
            cleanup_hooks=(self._release_camera,),
        )

    def _latest_frame_capture_boundary(self) -> CaptureBurstResult:
        with self._latest_frame_lock:
            frame = self._latest_frame
            recent_frames = list(self._recent_frames)
        if frame is None:
            self._log("CAPTURE_BOUNDARY_NO_FRAME", level="WARNING")
            return CaptureBurstResult(
                success=False,
                candidates=[],
                source_type=CameraSourceType.GENERIC_RGB,
                partial_timeout=False,
                error=CameraError(
                    CameraErrorCode.CAMERA_CAPTURE_TIMEOUT,
                    "No live camera frame is available yet.",
                    "Camera is warming up. Try again.",
                ),
                message="No live camera frame is available yet.",
                cleanup_status=CleanupStatus.NOT_REQUIRED,
            )

        frames = recent_frames or [(time.monotonic(), frame)]
        candidates: list[FrameCandidate] = []
        try:
            for index, (_captured_at, candidate_frame) in enumerate(frames):
                quality_report = assess_image_quality(
                    ImageInput(
                        image_array=_quality_analysis_image(candidate_frame),
                        source_id=f"runtime-recent-frame-{index}",
                    )
                )
                candidates.append(
                    FrameCandidate(
                        frame_id=f"runtime-recent-{index}-{int(time.time() * 1000)}",
                        rgb_image=candidate_frame,
                        depth_map=None,
                        timestamp=time.time(),
                        capture_order=index,
                        source_id=getattr(
                            self._camera_source,
                            "source_id",
                            "runtime-camera",
                        ),
                        quality_report=quality_report,
                        depth_report=None,
                        metadata={"source_type": CameraSourceType.GENERIC_RGB.value},
                    )
                )
        except Exception as exc:
            self._latest_quality_status = f"quality analysis failed: {type(exc).__name__}"
            self._log(
                "QUALITY_ANALYSIS_FAILED",
                error=type(exc).__name__,
                error_message=str(exc),
                level="WARNING",
            )
            return CaptureBurstResult(
                success=False,
                candidates=[],
                source_type=CameraSourceType.GENERIC_RGB,
                partial_timeout=False,
                error=CameraError(
                    CameraErrorCode.CAMERA_UNEXPECTED_ERROR,
                    "Frame quality analysis failed.",
                    "Camera preview is still running. Try again in a moment.",
                ),
                message="Frame quality analysis failed.",
                cleanup_status=CleanupStatus.NOT_REQUIRED,
            )

        selection = select_best_frame(
            candidates,
            source_type=CameraSourceType.GENERIC_RGB,
            partial_timeout=False,
            cleanup_status=CleanupStatus.NOT_REQUIRED,
        )
        selected = getattr(selection, "selected_frame", None) or max(
            candidates,
            key=lambda item: float(
                getattr(getattr(item, "quality_report", None), "quality_score", 0.0)
            ),
        )
        self._latest_quality_status = _quality_status(selected.quality_report)
        report = selected.quality_report
        self._log_capture_boundary_if_needed(report, selection)
        if not selection.success and self._capture_override_active:
            selection = BestFrameSelectionResult(
                success=True,
                selected_frame=selected,
                candidate_summaries=[candidate.safe_summary() for candidate in candidates],
                guidance="Capture override used the latest live frame.",
                source_type=CameraSourceType.GENERIC_RGB,
                partial_timeout=False,
                cleanup_status=CleanupStatus.NOT_REQUIRED,
            )
        return CaptureBurstResult(
            success=True,
            candidates=candidates,
            source_type=CameraSourceType.GENERIC_RGB,
            partial_timeout=False,
            message="Using the best recent live camera frame.",
            cleanup_status=CleanupStatus.NOT_REQUIRED,
            selection_result=selection,
        )

    def _log_capture_boundary_if_needed(self, report: Any, selection: Any) -> None:
        now = time.monotonic()
        text_status = getattr(getattr(report, "text_presence_status", None), "value", None)
        blur_status = getattr(getattr(report, "blur_status", None), "value", None)
        brightness_status = getattr(getattr(report, "brightness_status", None), "value", None)
        selection_success = getattr(selection, "success", None)
        signature = (
            f"{text_status}|{blur_status}|{brightness_status}|"
            f"{selection_success}|{self._capture_override_active}"
        )
        interval = 2.0 if self._state == RuntimeMode.SEARCHING_TEXT else 8.0
        if (
            signature == self._last_capture_boundary_log_signature
            and now - self._last_capture_boundary_log_at < interval
        ):
            return
        self._last_capture_boundary_log_signature = signature
        self._last_capture_boundary_log_at = now
        self._log(
            "CAPTURE_BOUNDARY_FRAME",
            quality_score=getattr(report, "quality_score", None),
            text_status=text_status,
            blur_status=blur_status,
            brightness_status=brightness_status,
            acceptable=getattr(report, "is_acceptable", None),
            selection_success=selection_success,
            override=self._capture_override_active,
        )

    def _ocr_boundary(self, image: Any) -> Any:
        modules = self._load_modules()
        self._state = RuntimeMode.OCR
        self._log("OCR_BOUNDARY_START")
        variants = modules["preprocessing"].create_preprocessing_variants(
            modules["image_models"].ImageInput(
                image_array=image,
                source_id="runtime-selected-frame",
            )
        )
        variant = variants.variants[
            modules["image_models"].PreprocessingVariantName.LOCAL_NATURAL
        ]
        image_path = _write_temp_capture(variant.image)
        try:
            gemini_allowed = self._gemini_ocr_allowed()
            ocr_space_allowed = bool(self.config.ocr_space_api_key) and not self.options.offline
            online_allowed = gemini_allowed or ocr_space_allowed
            preferred_online_engine = "gemini" if gemini_allowed else "online"
            self._state = RuntimeMode.OCR_ONLINE if online_allowed else RuntimeMode.OCR_LOCAL
            self._log(
                "OCR_CASCADE_START",
                online_allowed=online_allowed,
                high_accuracy=self.options.high_accuracy,
            )
            engines = {
                "local": modules["paddle"].PaddleOCREngine(),
                "emergency": modules["tesseract"].TesseractEngine(),
            }
            if gemini_allowed:
                engines["gemini"] = modules["gemini_ocr"].GeminiOCREngine(
                    api_key=self.config.gemini_api_key,
                    model=self.config.assistant_gemini_ocr_model,
                    timeout_seconds=self.config.assistant_gemini_ocr_timeout_seconds,
                )
            elif ocr_space_allowed:
                engines["online"] = modules["ocr_space"].OCRSpaceClient(
                    api_key=self.config.ocr_space_api_key
                )
            result = modules["ocr_cascade"].run_ocr_cascade(
                modules["ocr_cascade"].OCRCascadeRequest(
                    image=str(image_path),
                    language_hints=("ar", "en"),
                    allow_online=online_allowed,
                    allow_offline=self.config.assistant_gemini_ocr_fallback_local
                    or not online_allowed,
                    high_accuracy=self.options.high_accuracy,
                    quality_threshold=self.config.ocr_quality_threshold,
                    max_attempts_per_engine=self.config.ocr_max_attempts_per_engine,
                    sensitive_text_logging_enabled=self.config.sensitive_text_logging,
                ),
                engines,
                online_status_provider=lambda: online_allowed,
                preferred_online_engine=preferred_online_engine,
            )
            self._latest_ocr_attempts = _attempts_status(result)
            self._log(
                "OCR_CASCADE_DONE",
                success=getattr(result, "success", None),
                selected_engine=getattr(result, "selected_engine", None),
                attempts=self._latest_ocr_attempts,
                guidance=getattr(result, "guidance", ""),
            )
            for attempt in getattr(result, "attempts", []) or []:
                self._log(
                    "OCR_CASCADE_ATTEMPT",
                    engine=getattr(attempt, "engine_name", None),
                    status=getattr(getattr(attempt, "status", None), "value", None),
                    error_code=getattr(getattr(attempt, "error_code", None), "value", None),
                    duration_ms=getattr(attempt, "duration_ms", None),
                    provider_status=getattr(attempt, "safe_metadata", {}).get(
                        "status_code"
                    ),
                    provider_error_status=getattr(attempt, "safe_metadata", {}).get(
                        "provider_error_status"
                    ),
                    model=getattr(attempt, "safe_metadata", {}).get("model"),
                    quality_score=getattr(
                        getattr(attempt, "quality_report", None),
                        "quality_score",
                        None,
                    ),
                )
            selected_result = getattr(result, "selected_result", None)
            self._debug_print_text(
                "OCR selected raw text",
                getattr(selected_result, "raw_text", "") or getattr(result, "raw_text", ""),
            )
            return result
        finally:
            image_path.unlink(missing_ok=True)

    def _load_modules(self) -> dict[str, object]:
        if self._modules is None:
            self._modules = {
                "camera_models": importlib.import_module("modules.camera.camera_models"),
                "cleanup": importlib.import_module("modules.text.cleanup"),
                "dialogue": importlib.import_module("modules.assistant.dialogue_manager"),
                "image_models": importlib.import_module(
                    "modules.image_processing.image_models"
                ),
                "preprocessing": importlib.import_module(
                    "modules.image_processing.preprocessing"
                ),
                "ocr_cascade": importlib.import_module("modules.ocr.ocr_cascade"),
                "gemini_ocr": importlib.import_module("modules.ocr.gemini_ocr_engine"),
                "ocr_space": importlib.import_module("modules.ocr.ocr_space_client"),
                "paddle": importlib.import_module("modules.ocr.paddle_ocr_engine"),
                "reading": importlib.import_module("modules.assistant.reading_controller"),
                "tesseract": importlib.import_module("modules.ocr.tesseract_engine"),
                "translation_argos": importlib.import_module(
                    "modules.translation.argos_fallback"
                ),
                "translation_controller": importlib.import_module(
                    "modules.assistant.translation_controller"
                ),
                "gemini_translation": importlib.import_module(
                    "modules.translation.gemini_translation_engine"
                ),
                "translation_online": importlib.import_module(
                    "modules.translation.online_translation_stack"
                ),
                "libre_translate": importlib.import_module(
                    "modules.translation.libre_translate_client"
                ),
                "tts": importlib.import_module("modules.voice.tts_engine"),
                "edge_tts": importlib.import_module("modules.voice.edge_tts_engine"),
                "voice_models": importlib.import_module("modules.voice.voice_models"),
            }
        return self._modules

    def _speak_guidance_if_needed(self, result: object) -> None:
        guidance = str(getattr(result, "guidance", "") or "").strip()
        if not guidance:
            return
        controller = self._controller
        if controller is not None and guidance == getattr(controller, "last_guidance", ""):
            return
        is_successful_content_handoff = bool(getattr(result, "success", False)) and (
            hasattr(result, "capture_success") or hasattr(result, "translated_text")
        )
        if is_successful_content_handoff:
            return
        self._speak_text(guidance, language="en")

    def _speak_text(self, text: str, *, language: str) -> None:
        reading_controller = getattr(self.workflow, "reading_controller", None)
        engine = getattr(reading_controller, "engine", None)
        if engine is None:
            self._log("TTS_REQUEST_SKIPPED", reason="engine_missing", language=language, level="WARNING")
            return
        session = self._command_session
        set_tts_busy = getattr(session, "set_tts_busy", None)
        if callable(set_tts_busy):
            set_tts_busy(True)
        try:
            self._log(
                "TTS_REQUEST",
                engine=getattr(engine, "name", type(engine).__name__),
                language=language,
                operation=SpeechOperation.GUIDANCE,
                text=text,
            )
            speech = engine.speak(
                SpeechRequest(
                    text=text,
                    language=language,
                    operation=SpeechOperation.GUIDANCE,
                )
            )
            self._log(
                "TTS_RESULT",
                engine=getattr(speech, "engine_name", None),
                success=getattr(speech, "success", None),
                fallback_used=getattr(speech, "fallback_used", None),
                guidance=getattr(speech, "guidance", ""),
                error_code=getattr(getattr(speech, "error", None), "code", None),
            )
            if not getattr(speech, "success", False):
                print(f"Audio warning: {getattr(speech, 'guidance', 'TTS failed.')}")
        except Exception as exc:
            self._log("TTS_EXCEPTION", error=type(exc).__name__, language=language, level="ERROR")
            print(f"Audio warning: {type(exc).__name__}: {exc}")
        finally:
            if callable(set_tts_busy):
                set_tts_busy(False)

    def _set_voice_tts_busy(self, busy: bool) -> None:
        session = self._command_session
        set_tts_busy = getattr(session, "set_tts_busy", None)
        if callable(set_tts_busy):
            set_tts_busy(busy)

    @staticmethod
    def _print_result(result: object) -> None:
        guidance = getattr(result, "guidance", None)
        if guidance:
            print(guidance)
        else:
            print(result)

    def _render_gui(self, frame: Any) -> None:
        if not self.options.show_window or not self._gui_available:
            return
        if not hasattr(frame, "shape") or not hasattr(frame, "copy"):
            return
        try:
            import cv2
        except ImportError:
            self._gui_available = False
            print("OpenCV GUI is unavailable. Continuing without camera window.")
            return

        try:
            canvas = frame.copy()
            self._draw_overlay(cv2, canvas)
            cv2.imshow("Blind OCR Assistant Runtime", canvas)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                self.request_shutdown()
        except Exception as exc:
            self._gui_available = False
            print(f"OpenCV GUI disabled: {type(exc).__name__}: {exc}")

    def _draw_overlay(self, cv2: Any, frame: Any) -> None:
        height, width = frame.shape[:2]
        mode_color = self._mode_color()
        snapshot = self._snapshot_copy()
        readiness = snapshot.latest_frame_readiness
        active_job = snapshot.active_job
        voice_mode = getattr(self._command_session, "mode", "starting")
        voice_status = getattr(self._command_session, "last_status", "Starting voice.")
        voice_provider = getattr(getattr(self._command_session, "status", None), "provider", voice_mode)
        workflow_state = self._safe_workflow_state()

        panel_w = min(390, max(310, width // 2))
        self._draw_panel(cv2, frame, 12, 12, panel_w, 260, border=mode_color)
        self._draw_text(cv2, frame, "Blind OCR Assistant", 28, 42, 0.72, (245, 245, 245), 2)
        self._draw_badge(cv2, frame, self._state.value, 28, 58, mode_color)
        self._draw_metric(cv2, frame, "Camera", self._latest_camera_status, 28, 112)
        self._draw_metric(cv2, frame, "Quality", self._latest_quality_status, 28, 142)
        self._draw_metric(cv2, frame, "Voice", f"{voice_mode}: {voice_status}", 28, 172)
        self._draw_metric(cv2, frame, "Command", self._latest_command or "-", 28, 202)
        self._draw_metric(cv2, frame, "Guidance", snapshot.latest_guidance or "-", 28, 232)
        self._draw_metric(
            cv2,
            frame,
            "Last OCR",
            f"{getattr(workflow_state, 'last_ocr_engine', None) or '-'} / "
            f"{getattr(workflow_state, 'last_language', 'unknown')}",
            28,
            262,
        )

        right_w = min(310, max(250, width // 3))
        right_x = max(12, width - right_w - 12)
        self._draw_panel(cv2, frame, right_x, 12, right_w, 244, border=(80, 120, 180))
        self._draw_text(cv2, frame, "Runtime", right_x + 16, 40, 0.62, (245, 245, 245), 2)
        self._draw_metric(cv2, frame, "Mode", self.options.runtime_mode, right_x + 16, 76)
        self._draw_metric(cv2, frame, "Operation", self._latest_operation, right_x + 16, 106)
        self._draw_metric(cv2, frame, "Voice", str(voice_provider), right_x + 16, 136)
        self._draw_metric(
            cv2,
            frame,
            "Online",
            "available" if self._online_ocr_allowed() else "offline/local",
            right_x + 16,
            166,
        )
        self._draw_metric(
            cv2,
            frame,
            "Text",
            "ready" if readiness.ready_to_capture else ("visible" if readiness.has_text else "not found"),
            right_x + 16,
            196,
        )
        self._draw_metric(cv2, frame, "OCR", self._latest_ocr_attempts, right_x + 16, 226)

        checklist_y = 290
        self._draw_panel(cv2, frame, 12, checklist_y, panel_w, 150, border=(96, 150, 210))
        self._draw_text(cv2, frame, "Readiness", 28, checklist_y + 28, 0.58, (245, 245, 245), 2)
        self._draw_metric(cv2, frame, "Text", _yes_no(readiness.has_text), 28, checklist_y + 62)
        self._draw_metric(cv2, frame, "Stable", str(readiness.stable_frames), 28, checklist_y + 92)
        self._draw_metric(cv2, frame, "Light", _yes_no(readiness.brightness_ok), 28, checklist_y + 122)
        self._draw_metric(cv2, frame, "Sharp", _yes_no(readiness.blur_ok), 28, checklist_y + 152)

        if active_job is not None and active_job.finished_at is None:
            self._draw_metric(
                cv2,
                frame,
                "Job",
                f"{active_job.job_type.value}:{active_job.status.value}",
                right_x + 16,
                256,
            )

        bottom_text = "Q/Esc exit   Say or type: read text, translate to arabic, translate to english"
        self._draw_panel(cv2, frame, 12, height - 56, width - 24, 44, alpha=0.64)
        self._draw_text(cv2, frame, bottom_text, 28, height - 28, 0.52, (235, 240, 240), 1)

    def _safe_workflow_state(self) -> object:
        workflow = self._workflow
        getter = getattr(workflow, "get_state", None)
        if callable(getter):
            try:
                return getter()
            except Exception:
                return object()
        return object()

    def _mode_color(self) -> tuple[int, int, int]:
        if self._state == RuntimeMode.LISTENING:
            return (80, 210, 150)
        if self._state in {RuntimeMode.SEARCHING_TEXT, RuntimeMode.READY_TO_CAPTURE}:
            return (90, 220, 240)
        if self._state in {RuntimeMode.CAPTURING, RuntimeMode.OCR, RuntimeMode.ANALYZING}:
            return (0, 190, 255)
        if self._state in {RuntimeMode.READING, RuntimeMode.TRANSLATING}:
            return (255, 170, 70)
        if self._state == RuntimeMode.ERROR:
            return (60, 80, 255)
        return (165, 175, 185)

    @staticmethod
    def _draw_panel(
        cv2: Any,
        frame: Any,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        color: tuple[int, int, int] = (24, 28, 32),
        border: tuple[int, int, int] = (82, 92, 100),
        alpha: float = 0.76,
    ) -> None:
        height, width = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(width - 1, x + w), min(height - 1, y + h)
        if x2 <= x1 or y2 <= y1:
            return
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border, 1)

    @staticmethod
    def _draw_badge(
        cv2: Any,
        frame: Any,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)
        w, h = size
        cv2.rectangle(frame, (x, y), (x + w + 18, y + h + 14), color, -1)
        cv2.rectangle(frame, (x, y), (x + w + 18, y + h + 14), (255, 255, 255), 1)
        AssistantRuntime._draw_text(cv2, frame, text, x + 9, y + h + 8, 0.52, (12, 16, 18), 2)

    @staticmethod
    def _draw_metric(cv2: Any, frame: Any, label: str, value: str, x: int, y: int) -> None:
        AssistantRuntime._draw_text(cv2, frame, label, x, y, 0.45, (165, 176, 185), 1)
        AssistantRuntime._draw_text(
            cv2,
            frame,
            AssistantRuntime._shorten(value, 34),
            x + 96,
            y,
            0.50,
            (245, 248, 250),
            1,
        )

    @staticmethod
    def _draw_text(
        cv2: Any,
        frame: Any,
        text: str,
        x: int,
        y: int,
        scale: float,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 2)
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

    @staticmethod
    def _shorten(text: str, max_chars: int) -> str:
        text = str(text)
        if len(text) <= max_chars:
            return text
        return text[: max(0, max_chars - 3)] + "..."

    @staticmethod
    def _run_startup_checks() -> int:
        self_check = run_self_check()
        if not self_check.success:
            print(f"FAIL {self_check.error_code}: {self_check.message}")
            return 1
        report = run_lightweight_startup_diagnostics(local_fallback_available=True)
        print(format_report_for_cli(report))
        print(offline_recovery_spoken_summary(report.overall_status))
        if report.overall_status is ReadinessStatus.BLOCKED:
            return 1
        return 0

    def _print_runtime_readiness(self) -> None:
        tts_stack = "edge -> local" if self.options.tts_provider in {"auto", "edge", "online"} else "local"
        stt_stack = (
            "google_web -> vosk -> text"
            if self.options.stt_provider == "auto"
            else self.options.stt_provider
        )
        if self._gemini_ocr_allowed():
            ocr_stack = "gemini -> paddleocr -> tesseract"
        elif bool(self.config.ocr_space_api_key) and not self.options.offline:
            ocr_stack = "ocr.space -> paddleocr -> tesseract"
        else:
            ocr_stack = "paddleocr -> tesseract"
        translation_stack = (
            "gemini -> google -> mymemory"
            if (
                self.config.assistant_gemini_translation_enabled
                and self.config.gemini_api_key
                and not self.options.offline
            )
            else "google -> mymemory"
        )
        if self.config.libretranslate_url:
            translation_stack += " -> libretranslate"
        translation_stack += " -> argos"
        print("Runtime readiness:")
        print(f"- STT: {stt_stack}")
        print(f"- TTS: {tts_stack}")
        print(f"- OCR: {ocr_stack}")
        print(f"- Translation: {translation_stack}")

    def _gemini_ocr_allowed(self) -> bool:
        return bool(
            self.config.assistant_gemini_ocr_enabled
            and self.config.gemini_api_key
            and not self.options.offline
        )

    def _online_ocr_allowed(self) -> bool:
        return self._gemini_ocr_allowed() or bool(
            self.config.ocr_space_api_key and not self.options.offline
        )

    def _shutdown(self) -> None:
        self._state = RuntimeMode.SHUTDOWN
        self._update_snapshot(mode=RuntimeSystemMode.SHUTDOWN)
        self._job_worker.shutdown()
        self._audio_cues.stop()
        if self._command_session is not None:
            self._command_session.stop()
        if self._workflow is not None:
            self._workflow.shutdown()
        self._release_camera()
        self._close_gui()
        print("Assistant runtime stopped.")

    def _release_camera(self) -> None:
        try:
            self._camera_source.release()
        except Exception:
            pass

    def _close_gui(self) -> None:
        if not self.options.show_window or not self._gui_available:
            return
        try:
            import cv2

            cv2.destroyWindow("Blind OCR Assistant Runtime")
        except Exception:
            pass


class _FallbackTTSEngine:
    name = "runtime_tts_stack"
    supports_pause = False
    supports_resume = False

    def __init__(self, engines: list[Any], *, log_event: Callable[..., None] | None = None) -> None:
        self.engines = engines
        self.last_engine_name = ""
        self._log_event = log_event

    def speak(self, request: SpeechRequest) -> Any:
        last_result = None
        for index, engine in enumerate(self.engines):
            engine_name = getattr(engine, "name", type(engine).__name__)
            self._log(
                "TTS_ENGINE_ATTEMPT",
                engine=engine_name,
                language=request.language,
                operation=request.operation,
            )
            result = engine.speak(request)
            last_result = result
            self._log(
                "TTS_ENGINE_RESULT",
                engine=engine_name,
                success=getattr(result, "success", None),
                fallback_index=index,
                guidance=getattr(result, "guidance", ""),
                error_code=getattr(getattr(result, "error", None), "code", None),
            )
            if getattr(result, "success", False):
                self.last_engine_name = engine_name
                if index:
                    return result.__class__.ok(
                        operation=result.operation,
                        engine_name=result.engine_name,
                        duration_ms=result.duration_ms,
                        guidance=result.guidance,
                        fallback_used=True,
                    )
                return result
        return last_result

    def _log(self, event: str, /, **fields: Any) -> None:
        if self._log_event is None:
            return
        try:
            self._log_event(event, **fields)
        except Exception:
            pass

    def stop(self) -> Any:
        result = None
        for engine in self.engines:
            stop = getattr(engine, "stop", None)
            if callable(stop):
                result = stop()
        return result or self.engines[0].stop()

    def pause(self) -> Any:
        return self.engines[0].pause()

    def resume(self) -> Any:
        return self.engines[0].resume()


class _CueAwareReadingController:
    """Stop loading cues before audible reading starts."""

    def __init__(
        self,
        controller: Any,
        *,
        before_speak: Callable[[], None],
        set_tts_busy: Callable[[bool], None] | None = None,
    ) -> None:
        self._controller = controller
        self._before_speak = before_speak
        self._set_tts_busy = set_tts_busy
        self.engine = controller.engine

    def start_reading(self, *args: Any, **kwargs: Any) -> Any:
        self._before_speak()
        if self._set_tts_busy is not None:
            self._set_tts_busy(True)
        try:
            return self._controller.start_reading(*args, **kwargs)
        finally:
            if self._set_tts_busy is not None:
                self._set_tts_busy(False)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._controller, name)


def _build_tts_engine(
    *,
    modules: dict[str, object],
    tts_engine: str,
    tts_provider: str = "auto",
    ar_voice: str = "ar-EG-SalmaNeural",
    en_voice: str = "en-US-JennyNeural",
    log_event: Callable[..., None] | None = None,
) -> Any:
    if tts_engine == "mock":
        return modules["tts"].MockTTSEngine(name="runtime_mock_tts")
    local_engine = (
        modules["tts"].WindowsSapiEngine()
        if tts_engine == "windows" or (tts_engine == "auto" and os.name == "nt")
        else modules["tts"].EspeakNGEngine()
    )
    if tts_provider == "local":
        return local_engine
    if tts_provider in {"auto", "edge", "online"}:
        return _FallbackTTSEngine(
            [
                modules["edge_tts"].EdgeTTSEngine(
                    arabic_voice=ar_voice,
                    english_voice=en_voice,
                ),
                local_engine,
            ],
            log_event=log_event,
        )
    if tts_engine == "windows" or (tts_engine == "auto" and os.name == "nt"):
        return modules["tts"].WindowsSapiEngine()
    return modules["tts"].EspeakNGEngine()


def _resolve_vosk_model_path(voice_model: str | None) -> str:
    if voice_model:
        return voice_model
    return (
        os.getenv("VOSK_MODEL_EN")
        or os.getenv("VOSK_MODEL")
        or str(Path("models") / "vosk" / "vosk-model-small-en-us-0.15")
    )


def _is_runtime_exit_command(command: str) -> bool:
    return command.strip().lower() in {
        "exit",
        "quit",
        "shutdown",
        "close assistant",
        "stop assistant",
    }


def _quality_status(report: Any | None) -> str:
    if report is None:
        return "not checked"
    score = getattr(report, "quality_score", None)
    text_presence = getattr(getattr(report, "text_presence_status", None), "value", None)
    blur = getattr(getattr(report, "blur_status", None), "value", None)
    brightness = getattr(getattr(report, "brightness_status", None), "value", None)
    acceptable = getattr(report, "is_acceptable", None)
    score_text = f"{float(score):.2f}" if score is not None else "?"
    return (
        f"score {score_text}, text {text_presence or '?'}, "
        f"blur {blur or '?'}, light {brightness or '?'}, ok {bool(acceptable)}"
    )


def _quality_analysis_image(image: Any, *, max_side: int = 720) -> Any:
    """Return a smaller frame for cheap quality checks to avoid memory pressure."""
    shape = getattr(image, "shape", None)
    if not shape or len(shape) < 2:
        return image
    height, width = int(shape[0]), int(shape[1])
    longest = max(height, width)
    if longest <= max_side:
        return image
    scale = max_side / float(longest)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    import cv2

    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def _attempts_status(result: Any) -> str:
    attempts = list(getattr(result, "attempts", []) or [])
    if not attempts:
        return "-"
    labels = []
    for attempt in attempts[:3]:
        label = (
            f"{getattr(attempt, 'engine_name', '?')}:"
            f"{getattr(getattr(attempt, 'status', None), 'value', '?')}"
        )
        error_code = getattr(getattr(attempt, "error_code", None), "value", None)
        if error_code:
            label += f":{error_code}"
        status_code = getattr(attempt, "safe_metadata", {}).get("status_code")
        if status_code is not None:
            label += f":http={status_code}"
        provider_error_status = getattr(attempt, "safe_metadata", {}).get(
            "provider_error_status"
        )
        if provider_error_status:
            label += f":{provider_error_status}"
        labels.append(label)
    return " | ".join(labels)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _snapshot_mode_for_runtime(mode: RuntimeMode) -> RuntimeSystemMode:
    mapping = {
        RuntimeMode.LISTENING: RuntimeSystemMode.LISTENING,
        RuntimeMode.SEARCHING_TEXT: RuntimeSystemMode.SEARCHING_TEXT,
        RuntimeMode.READY_TO_CAPTURE: RuntimeSystemMode.READY_TO_CAPTURE,
        RuntimeMode.CAPTURING: RuntimeSystemMode.CAPTURING,
        RuntimeMode.ANALYZING: RuntimeSystemMode.OCR_RUNNING,
        RuntimeMode.OCR: RuntimeSystemMode.OCR_RUNNING,
        RuntimeMode.OCR_ONLINE: RuntimeSystemMode.OCR_RUNNING,
        RuntimeMode.OCR_LOCAL: RuntimeSystemMode.OCR_RUNNING,
        RuntimeMode.READING: RuntimeSystemMode.READING,
        RuntimeMode.TRANSLATING: RuntimeSystemMode.TRANSLATING,
        RuntimeMode.SPEAKING: RuntimeSystemMode.SPEAKING,
        RuntimeMode.ERROR: RuntimeSystemMode.ERROR,
        RuntimeMode.SHUTDOWN: RuntimeSystemMode.SHUTDOWN,
    }
    return mapping.get(mode, RuntimeSystemMode.LISTENING)


def _write_temp_capture(image: Any) -> Path:
    import tempfile

    import cv2

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image_path = Path(tmp.name)
    ok = cv2.imwrite(str(image_path), image)
    if not ok:
        image_path.unlink(missing_ok=True)
        raise RuntimeError("OpenCV could not write the captured frame")
    return image_path


__all__ = [
    "AssistantRuntime",
    "AssistantRuntimeOptions",
    "RuntimeCommandSession",
    "RuntimeMode",
]
