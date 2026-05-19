"""Full assistant workflow orchestration for Phase 9."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from modules.assistant.state import (
    AssistantSession,
    AssistantState,
    ReadWorkflowResult,
    TranslationWorkflowResult,
    WorkflowErrorCode,
    WorkflowFailure,
    WorkflowMode,
    WorkflowStatus,
)
from modules.voice.command_models import CommandIntent


@dataclass
class AssistantWorkflow:
    """Coordinate command, capture, OCR, cleanup, reading, and translation."""

    dialogue_manager: Any | None = None
    capture_burst: Callable[..., Any] | None = None
    select_best_frame: Callable[..., Any] | None = None
    run_ocr_cascade: Callable[..., Any] | None = None
    clean_ocr_text: Callable[..., Any] | None = None
    reading_controller: Any | None = None
    translation_controller: Any | None = None
    online_status_provider: Callable[[], bool] | None = None
    clock: Callable[[], float] = time.monotonic
    logger: Callable[..., Any] | None = None
    cleanup_hooks: Iterable[Callable[[], Any]] = ()
    session: AssistantSession = field(default_factory=AssistantSession)

    def get_state(self) -> AssistantState:
        """Return current assistant workflow state."""
        return self.session.state

    def handle_command(self, phrase: str, language_hint: str = "unknown") -> Any:
        """Recognize a command and route supported Phase 9 workflow intents."""
        if self.dialogue_manager is None:
            return self._missing_boundary(
                code=WorkflowErrorCode.COMMAND_UNAVAILABLE,
                guidance="Command handling is unavailable.",
                source="command",
            )
        result = self._call_boundary(
            self.dialogue_manager.handle_command,
            phrase,
            language_hint=language_hint,
            failure_code=WorkflowErrorCode.COMMAND_UNAVAILABLE,
            failure_guidance="Command handling failed. Try again.",
            failure_message="Command handling failed",
            source="command",
        )
        if isinstance(result, ReadWorkflowResult):
            self.session = self.session.with_updates(
                state=self.session.state.with_failure(result),
                last_result=result,
            )
            return result
        if not getattr(result, "success", False):
            return result
        if getattr(result, "intent", None) == CommandIntent.READ:
            return self.run_read_workflow()
        if getattr(result, "intent", None) in {
            CommandIntent.TRANSLATE_TO_ARABIC,
            CommandIntent.TRANSLATE_TO_ENGLISH,
        }:
            target_language = getattr(result, "target_language", None)
            if target_language is None:
                target_language = (
                    "ar"
                    if getattr(result, "intent", None) == CommandIntent.TRANSLATE_TO_ARABIC
                    else "en"
                )
            return self.run_translation_workflow(target_language)
        return result

    def run_read_workflow(self, *, high_accuracy: bool = False) -> ReadWorkflowResult:
        """Run command-to-capture-to-OCR-to-cleanup-to-reading workflow."""
        guard = self._read_guard()
        if guard is not None:
            return guard
        missing = self._first_missing_read_boundary()
        if missing is not None:
            return missing

        start = self.clock()
        self.session = self.session.with_updates(
            workflow_active=True,
            state=self.session.state.with_updates(
                current_mode=WorkflowMode.CAPTURING,
                last_guidance="Capturing image.",
            ),
        )
        try:
            capture_result = self._call_boundary(
                self.capture_burst,
                failure_code=WorkflowErrorCode.CAMERA_UNAVAILABLE,
                failure_guidance="Camera capture failed. Try again.",
                failure_message="Camera capture failed",
                source="camera",
            )
            if isinstance(capture_result, ReadWorkflowResult):
                return self._record_read_failure(capture_result)
            if not getattr(capture_result, "success", False):
                capture_error = getattr(capture_result, "error", None)
                return self._record_read_failure(
                    self._failure_result(
                        self._camera_failure_code(capture_error),
                        "Camera capture failed.",
                        getattr(capture_result, "message", "")
                        or getattr(capture_error, "guidance", None)
                        or "Camera capture failed. Try again.",
                        source="camera",
                    )
                )

            self.session = self.session.with_updates(
                state=self.session.state.with_updates(
                    current_mode=WorkflowMode.SELECTING_FRAME,
                    last_guidance="Selecting the clearest frame.",
                )
            )
            selection_result = getattr(capture_result, "selection_result", None)
            if selection_result is None and self.select_best_frame is not None:
                selection_result = self._call_boundary(
                    self.select_best_frame,
                    getattr(capture_result, "candidates", []),
                    failure_code=WorkflowErrorCode.NO_ACCEPTABLE_FRAME,
                    failure_guidance="Recapture the image more clearly.",
                    failure_message="Best frame selection failed",
                    source="camera",
                )
            if isinstance(selection_result, ReadWorkflowResult):
                return self._record_read_failure(selection_result)
            if not getattr(selection_result, "success", False):
                return self._record_read_failure(
                    self._failure_result(
                        WorkflowErrorCode.NO_ACCEPTABLE_FRAME,
                        "No acceptable frame was selected.",
                        getattr(selection_result, "guidance", "")
                        or "Recapture the image more clearly.",
                        source="camera",
                    )
                )

            selected_frame = getattr(selection_result, "selected_frame", None)
            image = getattr(selected_frame, "rgb_image", selected_frame)

            self.session = self.session.with_updates(
                state=self.session.state.with_updates(
                    current_mode=WorkflowMode.OCR,
                    last_guidance="Reading text from the image.",
                )
            )
            ocr_result = self._call_boundary(
                self.run_ocr_cascade,
                image,
                failure_code=WorkflowErrorCode.OCR_FAILED,
                failure_guidance="I could not read the text clearly. Please try again.",
                failure_message="OCR failed",
                source="ocr",
            )
            if isinstance(ocr_result, ReadWorkflowResult):
                return self._record_read_failure(ocr_result)
            if not getattr(ocr_result, "success", False):
                return self._record_read_failure(
                    self._failure_result(
                        WorkflowErrorCode.OCR_FAILED,
                        "OCR failed.",
                        getattr(ocr_result, "guidance", "")
                        or "I could not read the text clearly. Please try again.",
                        source="ocr",
                    )
                )

            selected_ocr = getattr(ocr_result, "selected_result", None)
            raw_text = getattr(selected_ocr, "raw_text", "") or getattr(
                ocr_result, "raw_text", ""
            )
            selected_engine = getattr(ocr_result, "selected_engine", None) or getattr(
                selected_ocr, "engine_name", None
            )

            self.session = self.session.with_updates(
                state=self.session.state.with_updates(
                    current_mode=WorkflowMode.CLEANING,
                    last_guidance="Preparing text for reading.",
                )
            )
            cleanup_result = self._call_boundary(
                self.clean_ocr_text,
                raw_text,
                failure_code=WorkflowErrorCode.CLEANUP_EMPTY_TEXT,
                failure_guidance="No readable text was available after cleanup.",
                failure_message="Text cleanup failed",
                source="cleanup",
            )
            if isinstance(cleanup_result, ReadWorkflowResult):
                return self._record_read_failure(cleanup_result)
            clean_text = getattr(cleanup_result, "clean_text", "")
            if not getattr(cleanup_result, "success", False) or not clean_text.strip():
                return self._record_read_failure(
                    self._failure_result(
                        WorkflowErrorCode.CLEANUP_EMPTY_TEXT,
                        "Text cleanup produced no readable text.",
                        getattr(cleanup_result, "guidance", "")
                        or "No readable text was available.",
                        source="cleanup",
                    )
                )

            language = self._language_value(getattr(cleanup_result, "language", "unknown"))
            speech_result = self._call_boundary(
                self.reading_controller.start_reading,
                clean_text,
                language=language,
                failure_code=WorkflowErrorCode.TTS_FAILED,
                failure_guidance="Reading could not start.",
                failure_message="TTS failed",
                source="tts",
            )
            if isinstance(speech_result, ReadWorkflowResult):
                return self._record_read_failure(speech_result)
            if not getattr(speech_result, "success", False):
                return self._record_read_failure(
                    self._failure_result(
                        WorkflowErrorCode.TTS_FAILED,
                        "TTS failed.",
                        getattr(speech_result, "guidance", "")
                        or "Reading could not start.",
                        source="tts",
                    )
                )

            duration_ms = self._duration_ms(start)
            guidance = self._read_success_guidance(ocr_result)
            result = ReadWorkflowResult.ok(
                selected_ocr_engine=selected_engine or "unknown",
                language=language,
                fallback_used=bool(getattr(ocr_result, "fallback_used", False)),
                offline_route_used=bool(getattr(ocr_result, "offline_route_used", False)),
                high_accuracy_used=bool(getattr(ocr_result, "high_accuracy_used", high_accuracy)),
                duration_ms=duration_ms,
                guidance=guidance,
                raw_text=raw_text,
                clean_text=clean_text,
            )
            state = self.session.state.with_successful_read(
                raw_text=raw_text,
                clean_text=clean_text,
                language=language,
                selected_ocr_engine=result.selected_ocr_engine,
                fallback_used=result.fallback_used,
                guidance=result.guidance,
                result=result,
            )
            self.session = self.session.with_updates(
                state=state,
                workflow_active=False,
                last_result=result,
            )
            return result
        finally:
            if not self.session.shutdown_requested and self.session.workflow_active:
                self.session = self.session.with_updates(workflow_active=False)

    def run_translation_workflow(self, target_language: str) -> TranslationWorkflowResult:
        """Translate latest clean text through the injected translation boundary."""
        if self.session.shutdown_requested:
            failure = WorkflowFailure(
                WorkflowErrorCode.SHUTDOWN_REQUESTED,
                "Shutdown has been requested.",
                "Assistant is shutting down.",
                recoverable=False,
                source="shutdown",
            )
            return TranslationWorkflowResult.failure(
                target_language=target_language,
                source_language=self.session.state.last_language,
                error=failure,
                status=WorkflowStatus.SHUTDOWN,
            )
        clean_text = self.session.state.last_clean_text.strip()
        if not clean_text:
            failure = WorkflowFailure(
                WorkflowErrorCode.TRANSLATION_UNAVAILABLE,
                "No latest clean text is available for translation.",
                "No readable text is available to translate.",
                source="translation",
            )
            result = TranslationWorkflowResult.failure(
                target_language=target_language,
                source_language=self.session.state.last_language,
                error=failure,
                status=WorkflowStatus.UNAVAILABLE,
            )
            self.session = self.session.with_updates(
                state=self.session.state.with_failure(result),
                last_result=result,
            )
            return result
        if self.translation_controller is None or not hasattr(
            self.translation_controller,
            "translate_latest",
        ):
            failure = WorkflowFailure(
                WorkflowErrorCode.TRANSLATION_UNAVAILABLE,
                "Translation boundary is unavailable.",
                "Translation is unavailable.",
                source="translation",
            )
            result = TranslationWorkflowResult.failure(
                target_language=target_language,
                source_language=self.session.state.last_language,
                error=failure,
                status=WorkflowStatus.UNAVAILABLE,
            )
            self.session = self.session.with_updates(
                state=self.session.state.with_failure(result),
                last_result=result,
            )
            return result

        start = self.clock()
        self.session = self.session.with_updates(
            state=self.session.state.with_updates(
                current_mode=WorkflowMode.TRANSLATING,
                last_guidance="Translation is starting.",
            )
        )
        translation_result = self._call_boundary(
            self.translation_controller.translate_latest,
            clean_text,
            target_language,
            source_language=self.session.state.last_language,
            allow_online=True,
            allow_offline=True,
            failure_code=WorkflowErrorCode.TRANSLATION_FAILED,
            failure_guidance="Translation failed. Try again.",
            failure_message="Translation failed",
            source="translation",
        )
        if isinstance(translation_result, ReadWorkflowResult):
            failure = translation_result.error or WorkflowFailure(
                WorkflowErrorCode.TRANSLATION_FAILED,
                "Translation failed.",
                translation_result.guidance,
                source="translation",
            )
            result = TranslationWorkflowResult.failure(
                target_language=target_language,
                source_language=self.session.state.last_language,
                error=failure,
                guidance=translation_result.guidance,
                duration_ms=translation_result.duration_ms,
            )
            self.session = self.session.with_updates(
                state=self.session.state.with_failure(result),
                last_result=result,
            )
            return result

        if not getattr(translation_result, "success", False):
            failure = WorkflowFailure(
                WorkflowErrorCode.TRANSLATION_FAILED,
                "Translation failed.",
                getattr(translation_result, "guidance", "")
                or "Translation failed. Try again.",
                source="translation",
            )
            result = TranslationWorkflowResult.failure(
                target_language=target_language,
                source_language=self.session.state.last_language,
                error=failure,
                fallback_used=bool(getattr(translation_result, "fallback_used", False)),
                duration_ms=self._duration_ms(start),
            )
            self.session = self.session.with_updates(
                state=self.session.state.with_failure(result),
                last_result=result,
            )
            return result

        translated_text = getattr(translation_result, "translated_text", "")
        result = TranslationWorkflowResult.ok(
            target_language=getattr(translation_result, "target_language", target_language),
            source_language=getattr(
                translation_result,
                "source_language",
                self.session.state.last_language,
            ),
            translated_text=translated_text,
            fallback_used=bool(getattr(translation_result, "fallback_used", False)),
            reading_handoff_attempted=bool(
                getattr(translation_result, "reading_handoff_attempted", False)
            ),
            reading_handoff_success=bool(
                getattr(translation_result, "reading_handoff_success", False)
            ),
            duration_ms=getattr(translation_result, "duration_ms", None)
            or self._duration_ms(start),
            guidance=getattr(translation_result, "guidance", "")
            or "The translated text is being read.",
        )
        self.session = self.session.with_updates(
            state=self.session.state.with_successful_translation(
                translated_text=translated_text,
                guidance=result.guidance,
                result=result,
            ),
            last_result=result,
        )
        return result

    def shutdown(self) -> ReadWorkflowResult:
        """Request operational shutdown and run cleanup hooks."""
        cleanup_error: WorkflowFailure | None = None
        stop_speech = getattr(self.reading_controller, "stop", None)
        if callable(stop_speech):
            try:
                stop_speech()
            except Exception:
                cleanup_error = WorkflowFailure(
                    WorkflowErrorCode.RESOURCE_RELEASE_FAILED,
                    "Speech cleanup failed during shutdown.",
                    "Assistant stopped, but speech cleanup reported a problem.",
                    source="shutdown",
                )
        for hook in self.cleanup_hooks:
            try:
                hook()
            except Exception:
                cleanup_error = WorkflowFailure(
                    WorkflowErrorCode.RESOURCE_RELEASE_FAILED,
                    "A cleanup hook failed during shutdown.",
                    "Assistant stopped, but resource cleanup reported a problem.",
                    source="shutdown",
                )
        self.session = self.session.request_shutdown()
        if cleanup_error is not None:
            result = ReadWorkflowResult.failure(
                error=cleanup_error,
                status=WorkflowStatus.SHUTDOWN,
            )
            self.session = self.session.with_updates(last_result=result)
            return result
        result = ReadWorkflowResult(
            success=True,
            status=WorkflowStatus.SHUTDOWN,
            guidance="Assistant stopped.",
        )
        self.session = self.session.with_updates(last_result=result)
        return result

    def _read_guard(self) -> ReadWorkflowResult | None:
        if self.session.shutdown_requested:
            failure = WorkflowFailure(
                WorkflowErrorCode.SHUTDOWN_REQUESTED,
                "Shutdown has been requested.",
                "Assistant is shutting down.",
                recoverable=False,
                source="shutdown",
            )
            return ReadWorkflowResult.failure(
                error=failure,
                status=WorkflowStatus.SHUTDOWN,
            )
        if self.session.workflow_active:
            failure = WorkflowFailure(
                WorkflowErrorCode.WORKFLOW_BUSY,
                "A read workflow is already active.",
                "I am already reading. Please wait, or use a playback command.",
                source="workflow",
            )
            return ReadWorkflowResult.failure(
                error=failure,
                status=WorkflowStatus.BUSY,
            )
        return None

    def _call_boundary(
        self,
        boundary: Callable[..., Any],
        *args: Any,
        failure_code: WorkflowErrorCode,
        failure_guidance: str,
        failure_message: str,
        source: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call an injected boundary and convert expected failures."""
        try:
            return boundary(*args, **kwargs)
        except KeyboardInterrupt:
            raise
        except TimeoutError:
            failure = WorkflowFailure(
                WorkflowErrorCode.COMPONENT_TIMEOUT,
                failure_message,
                failure_guidance,
                source=source,
            )
            return ReadWorkflowResult.failure(error=failure)
        except Exception:
            failure = WorkflowFailure(
                failure_code,
                failure_message,
                failure_guidance,
                source=source,
            )
            return ReadWorkflowResult.failure(error=failure)

    @staticmethod
    def _missing_boundary(
        *,
        code: WorkflowErrorCode,
        guidance: str,
        source: str,
    ) -> ReadWorkflowResult:
        failure = WorkflowFailure(
            code,
            f"{source} boundary is unavailable.",
            guidance,
            source=source,
        )
        return ReadWorkflowResult.failure(
            error=failure,
            status=WorkflowStatus.UNAVAILABLE,
        )

    def _first_missing_read_boundary(self) -> ReadWorkflowResult | None:
        required = (
            (self.capture_burst, WorkflowErrorCode.CAMERA_UNAVAILABLE, "Camera is unavailable.", "camera"),
            (self.run_ocr_cascade, WorkflowErrorCode.OCR_FAILED, "OCR is unavailable.", "ocr"),
            (self.clean_ocr_text, WorkflowErrorCode.CLEANUP_EMPTY_TEXT, "Text cleanup is unavailable.", "cleanup"),
            (
                getattr(self.reading_controller, "start_reading", None),
                WorkflowErrorCode.TTS_UNAVAILABLE,
                "Reading is unavailable.",
                "tts",
            ),
        )
        for boundary, code, guidance, source in required:
            if boundary is None:
                return self._missing_boundary(code=code, guidance=guidance, source=source)
        return None

    def _record_read_failure(self, result: ReadWorkflowResult) -> ReadWorkflowResult:
        self.session = self.session.with_updates(
            workflow_active=False,
            state=self.session.state.with_failure(result),
            last_result=result,
        )
        return result

    @staticmethod
    def _failure_result(
        code: WorkflowErrorCode,
        message: str,
        guidance: str,
        *,
        source: str,
    ) -> ReadWorkflowResult:
        return ReadWorkflowResult.failure(
            error=WorkflowFailure(code, message, guidance, source=source),
            status=WorkflowStatus.UNAVAILABLE
            if code
            in {
                WorkflowErrorCode.CAMERA_UNAVAILABLE,
                WorkflowErrorCode.TTS_UNAVAILABLE,
            }
            else WorkflowStatus.FAILED,
        )

    @staticmethod
    def _language_value(value: Any) -> str:
        raw = getattr(value, "value", value)
        mapping = {
            "arabic": "ar",
            "english": "en",
            "mixed": "mixed",
            "unknown": "unknown",
            "ar": "ar",
            "en": "en",
        }
        return mapping.get(str(raw).lower(), "unknown")

    def _duration_ms(self, start: float) -> int:
        try:
            return max(0, int((self.clock() - start) * 1000))
        except Exception:
            return 0

    @staticmethod
    def _read_success_guidance(ocr_result: Any) -> str:
        if bool(getattr(ocr_result, "fallback_used", False)):
            return "OCR text is ready after fallback OCR. Reading is starting."
        if bool(getattr(ocr_result, "offline_route_used", False)):
            return "OCR text is ready using the offline route. Reading is starting."
        return "Reading is starting."

    @staticmethod
    def _camera_failure_code(error: Any) -> WorkflowErrorCode:
        raw = getattr(getattr(error, "error_code", None), "value", None) or getattr(
            error,
            "error_code",
            "",
        )
        if str(raw) == "CAMERA_CAPTURE_TIMEOUT":
            return WorkflowErrorCode.CAPTURE_TIMEOUT
        return WorkflowErrorCode.CAMERA_UNAVAILABLE


__all__ = [
    "AssistantWorkflow",
]
