"""Event-driven controller for the integrated assistant runtime."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any

from modules.assistant.capture_gate import CaptureGate
from modules.assistant.job_worker import JobWorker
from modules.assistant.runtime_state import (
    FrameReadiness,
    RuntimeJob,
    RuntimeJobType,
)
from modules.voice.command_models import CommandIntent
from modules.voice.command_parser import CommandParser


class RuntimeControllerMode(str, Enum):
    LISTENING = "LISTENING"
    SEARCHING_TEXT = "SEARCHING_TEXT"
    READY_TO_CAPTURE = "READY_TO_CAPTURE"
    CAPTURING = "CAPTURING"
    ANALYZING = "ANALYZING"
    OCR_ONLINE = "OCR_ONLINE"
    OCR_LOCAL = "OCR_LOCAL"
    TRANSLATING = "TRANSLATING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


@dataclass
class RuntimeController:
    """Command router and read-when-ready state machine."""

    workflow: Any
    capture_preview: Callable[[], Any]
    speak: Callable[[str, str], None]
    set_mode: Callable[[RuntimeControllerMode], None]
    start_cue: Callable[[str], None]
    stop_cue: Callable[[], None]
    parser: CommandParser | None = None
    job_worker: JobWorker | None = None
    capture_gate: CaptureGate | None = None
    set_capture_override: Callable[[bool], None] | None = None
    on_job_result: Callable[[Any], None] | None = None
    on_guidance: Callable[[str], None] | None = None
    on_language_change: Callable[[str], None] | None = None
    log_event: Callable[..., None] | None = None
    guided_capture_enabled: bool = True
    guided_capture_timeout_seconds: float = 8.0
    guidance_cooldown_seconds: float = 3.0
    quiet_mode: bool = False
    verbose_mode: bool = False
    language: str = "auto"
    last_guidance: str = ""

    def __post_init__(self) -> None:
        if self.parser is None:
            self.parser = CommandParser()
        if self.job_worker is None:
            self.job_worker = JobWorker()
        if self.capture_gate is None:
            self.capture_gate = CaptureGate()
        self._waiting_for_text = False
        self._pending_high_accuracy = False
        self._last_guidance_code = ""
        self._last_guidance_spoken_at = 0.0
        self._latest_readiness = FrameReadiness()
        self._last_read_result: Any | None = None
        self._search_started_at = 0.0

    @property
    def waiting_for_text(self) -> bool:
        return self._waiting_for_text

    def handle_command(self, command: str, *, high_accuracy: bool = False) -> Any:
        parsed = self.parser.parse_text(command)
        self._log(
            "CONTROLLER_COMMAND_PARSED",
            success=parsed.success,
            intent=parsed.intent,
            confidence=parsed.confidence,
        )
        if not parsed.success:
            return self._workflow_command(command, high_accuracy=high_accuracy)
        if parsed.intent == CommandIntent.READ:
            return self._start_searching(high_accuracy=high_accuracy)
        if parsed.intent == CommandIntent.CAPTURE_NOW:
            return self._submit_read_job(high_accuracy=high_accuracy, override=True)
        if parsed.intent in {
            CommandIntent.TRANSLATE_TO_ARABIC,
            CommandIntent.TRANSLATE_TO_ENGLISH,
        }:
            return self._submit_translation_job(
                command,
                target=parsed.target_language,
                command_language=parsed.language,
            )
        if parsed.intent == CommandIntent.CANCEL:
            return self._cancel()
        if parsed.intent == CommandIntent.STATUS:
            return self._speak_result(self._status_message())
        if parsed.intent == CommandIntent.WHAT_DO_YOU_SEE:
            return self._speak_result(self._frame_description())
        if parsed.intent == CommandIntent.REPEAT_GUIDANCE:
            return self._speak_result(self.last_guidance or self._latest_readiness.guidance)
        if parsed.intent == CommandIntent.READ_AGAIN:
            return self._workflow_command("repeat paragraph", high_accuracy=high_accuracy)
        if parsed.intent == CommandIntent.QUIET_MODE:
            self.quiet_mode = True
            self.verbose_mode = False
            return self._speak_result("هقلل الكلام.", language="ar")
        if parsed.intent == CommandIntent.VERBOSE_MODE:
            self.quiet_mode = False
            self.verbose_mode = True
            return self._speak_result("هشرح أكتر.", language="ar")
        if parsed.intent == CommandIntent.VOICE_TEST:
            self._say("English voice test.", language="en")
            self._say("اختبار الصوت العربي.", language="ar")
            return _SimpleRuntimeResult(True, "Voice test completed.")
        if parsed.intent == CommandIntent.SWITCH_ARABIC:
            self.language = "ar"
            if self.on_language_change is not None:
                self.on_language_change("ar")
            return self._speak_result("تم تفعيل اللغة العربية.", language="ar")
        if parsed.intent == CommandIntent.SWITCH_ENGLISH:
            self.language = "en"
            if self.on_language_change is not None:
                self.on_language_change("en")
            return self._speak_result("English enabled.", language="en")
        if parsed.intent == CommandIntent.HELP:
            return self._speak_result(parsed.guidance)
        if parsed.intent == CommandIntent.EXIT:
            return parsed
        return self._workflow_command(command, high_accuracy=high_accuracy)

    def on_frame_readiness(self, readiness: FrameReadiness) -> None:
        """Advance pending read flow when the preview becomes capture-ready."""
        self._latest_readiness = readiness
        if not self._waiting_for_text:
            return
        self._log(
            "CONTROLLER_READINESS",
            has_text=readiness.has_text,
            ready=readiness.ready_to_capture,
            stable_frames=readiness.stable_frames,
            guidance_code=readiness.guidance_code,
        )
        if self.capture_gate and self.capture_gate.can_capture(readiness):
            self._waiting_for_text = False
            self.set_mode(RuntimeControllerMode.READY_TO_CAPTURE)
            self._log("READ_GATE_OPEN", guidance_code=readiness.guidance_code)
            self._say(readiness.guidance or "النص واضح. بصور دلوقتي.")
            self._submit_read_job(
                high_accuracy=self._pending_high_accuracy,
                override=readiness.guidance_code == "ready_low_quality",
            )
            return
        if self._should_timeout_capture(readiness):
            self._waiting_for_text = False
            self.set_mode(RuntimeControllerMode.READY_TO_CAPTURE)
            self._log("READ_GATE_TIMEOUT_CAPTURE", stable_frames=readiness.stable_frames)
            self._say("النص ظاهر. هاخد أحسن لقطة متاحة.", language="ar")
            self._submit_read_job(high_accuracy=self._pending_high_accuracy, override=True)
            return
        self._maybe_say_guidance(readiness)

    def _start_searching(self, *, high_accuracy: bool) -> Any:
        self._waiting_for_text = True
        self._pending_high_accuracy = high_accuracy
        self._search_started_at = time.monotonic()
        self.set_mode(RuntimeControllerMode.SEARCHING_TEXT)
        self._log("READ_SEARCH_STARTED", high_accuracy=high_accuracy)
        message = "حط النص قدام الكاميرا. هقرأ لما يبقى واضح."
        self._last_guidance_code = "no_text"
        self._last_guidance_spoken_at = time.monotonic()
        self._say(message, language="ar")
        return _SimpleRuntimeResult(True, message)

    def _submit_read_job(self, *, high_accuracy: bool, override: bool = False) -> Any:
        if self.job_worker and self.job_worker.active_job is not None:
            active = self.job_worker.active_job
            if active and active.finished_at is None:
                return _SimpleRuntimeResult(False, "Another operation is already running.")
        if override and self.capture_gate and not self.capture_gate.can_capture(
            self._latest_readiness,
            override=True,
        ):
            return _SimpleRuntimeResult(False, "Capture override is disabled.")

        self._waiting_for_text = False
        self.set_mode(RuntimeControllerMode.ANALYZING)
        self._log("READ_JOB_SUBMIT", high_accuracy=high_accuracy, override=override)
        if override:
            self._say("بصور دلوقتي. الدقة ممكن تكون أقل.", language="ar")
        else:
            self._say("بحلل النص.", language="ar")
        self.start_cue("ocr")

        def _run() -> Any:
            if self.set_capture_override is not None:
                self.set_capture_override(override)
            try:
                self._log("READ_JOB_RUN", override=override)
                return self.workflow.run_read_workflow(high_accuracy=high_accuracy)
            finally:
                if self.set_capture_override is not None:
                    self.set_capture_override(False)

        def _done(_job: RuntimeJob, result: Any | None) -> None:
            self.stop_cue()
            self._log(
                "READ_JOB_DONE",
                job_status=getattr(_job, "status", None),
                success=getattr(result, "success", None),
                guidance=getattr(result, "guidance", "") if result is not None else "",
            )
            if result is None:
                self.set_mode(RuntimeControllerMode.ERROR)
                self._say("القراءة فشلت.", language="ar")
                return
            self._last_read_result = result
            self.last_guidance = str(getattr(result, "guidance", "") or "")
            if self.on_job_result is not None:
                self.on_job_result(result)
            self.set_mode(
                RuntimeControllerMode.LISTENING
                if getattr(result, "success", False)
                else RuntimeControllerMode.ERROR
            )
            if not getattr(result, "success", False):
                self._say(self.last_guidance or "I could not read the text clearly.")
            else:
                print(self.last_guidance or "Reading completed.")

        self.job_worker.submit(
            RuntimeJobType.OCR,
            _run,
            progress_label="Analyzing text",
            on_complete=_done,
        )
        return _SimpleRuntimeResult(True, "OCR job started.")

    def _submit_translation_job(
        self,
        command: str,
        *,
        target: str | None,
        command_language: str = "unknown",
    ) -> Any:
        if self.job_worker and self.job_worker.active_job is not None:
            active = self.job_worker.active_job
            if active and active.finished_at is None:
                return _SimpleRuntimeResult(False, "Another operation is already running.")
        self.set_mode(RuntimeControllerMode.TRANSLATING)
        self._log("TRANSLATION_JOB_SUBMIT", target=target)
        guidance_language = command_language if command_language in {"ar", "en"} else "en"
        self._say(
            "بترجم دلوقتي." if guidance_language == "ar" else "Translating now.",
            language=guidance_language,
        )
        self.start_cue("translation")

        def _done(_job: RuntimeJob, result: Any | None) -> None:
            self.stop_cue()
            self._log(
                "TRANSLATION_JOB_DONE",
                job_status=getattr(_job, "status", None),
                success=getattr(result, "success", None),
                guidance=getattr(result, "guidance", "") if result is not None else "",
            )
            if result is not None and self.on_job_result is not None:
                self.on_job_result(result)
            guidance = getattr(result, "guidance", "") if result is not None else ""
            self.set_mode(
                RuntimeControllerMode.LISTENING
                if result is not None and getattr(result, "success", False)
                else RuntimeControllerMode.ERROR
            )
            if result is None or not getattr(result, "success", False):
                self._say(guidance or "Translation could not be completed.")
            else:
                print(guidance or "Translation completed.")
                if not getattr(result, "reading_handoff_success", False):
                    self._say(guidance or "Translation is ready.")

        self.job_worker.submit(
            RuntimeJobType.TRANSLATION,
            lambda: self._workflow_command(command, high_accuracy=False),
            progress_label=f"Translating to {target or 'target language'}",
            on_complete=_done,
        )
        return _SimpleRuntimeResult(True, "Translation job started.")

    def _cancel(self) -> Any:
        self._waiting_for_text = False
        self.stop_cue()
        self._log("OPERATION_CANCELLED")
        if self.job_worker is not None:
            self.job_worker.cancel_active()
        reading = getattr(self.workflow, "reading_controller", None)
        stopper = getattr(reading, "stop", None)
        if callable(stopper):
            try:
                stopper()
            except Exception:
                pass
        self.set_mode(RuntimeControllerMode.LISTENING)
        return self._speak_result("Operation cancelled.")

    def _workflow_command(self, command: str, *, high_accuracy: bool) -> Any:
        return self.workflow.handle_command(command, high_accuracy=high_accuracy)

    def _status_message(self) -> str:
        state = getattr(self.workflow, "get_state", lambda: None)()
        language = getattr(state, "last_language", "unknown") if state is not None else "unknown"
        has_text = bool(getattr(state, "last_clean_text", "")) if state is not None else False
        job = self.job_worker.active_job if self.job_worker is not None else None
        job_text = f" Active job: {job.job_type.value} {job.status.value}." if job else ""
        return (
            f"Assistant is running. Text ready: {has_text}. "
            f"Last language: {language}. {self._frame_description()}.{job_text}"
        )

    def _frame_description(self) -> str:
        readiness = self._latest_readiness
        if readiness.ready_to_capture:
            return "Text is clear and ready to capture"
        if readiness.has_text:
            return f"Text is visible but not ready yet. {readiness.guidance}"
        return readiness.guidance or "No clear text is visible yet"

    def _maybe_say_guidance(self, readiness: FrameReadiness) -> None:
        now = time.monotonic()
        changed = readiness.guidance_code != self._last_guidance_code
        repeat_seconds = max(self.guidance_cooldown_seconds, 6.0)
        if readiness.guidance_code == "no_text":
            repeat_seconds = max(repeat_seconds, 10.0)
        if not changed and now - self._last_guidance_spoken_at < repeat_seconds:
            return
        self._last_guidance_code = readiness.guidance_code
        self._last_guidance_spoken_at = now
        self._say(readiness.guidance)

    def _should_timeout_capture(self, readiness: FrameReadiness) -> bool:
        if not readiness.has_text:
            return False
        if readiness.stable_frames < 2:
            return False
        elapsed = time.monotonic() - self._search_started_at
        return elapsed >= max(1.0, self.guided_capture_timeout_seconds)

    def _speak_result(self, message: str, *, language: str | None = None) -> _SimpleRuntimeResult:
        self._say(message, language=language)
        return _SimpleRuntimeResult(True, message)

    def _say(self, text: str, *, language: str | None = None) -> None:
        self.last_guidance = text
        if self.on_guidance is not None:
            self.on_guidance(text)
        if self.quiet_mode and not self.verbose_mode:
            self._log("SPEAK_SKIPPED_QUIET", language=language or self._voice_language_for(text))
            return
        self._log("SPEAK_GUIDANCE", language=language or self._voice_language_for(text), text=text)
        self.speak(text, language or self._voice_language_for(text))

    def _voice_language_for(self, text: str) -> str:
        if self.language in {"ar", "en"}:
            return self.language
        return "ar" if any("\u0600" <= char <= "\u06ff" for char in text) else "en"

    def _log(self, event: str, /, **fields: Any) -> None:
        if self.log_event is None:
            return
        try:
            self.log_event(event, **fields)
        except Exception:
            pass


@dataclass(frozen=True)
class _SimpleRuntimeResult:
    success: bool
    guidance: str


__all__ = ["RuntimeController", "RuntimeControllerMode"]
