"""Tests for the integrated assistant runtime."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np

import modules.assistant.runtime as runtime_module
from modules.assistant.runtime import (
    AssistantRuntime,
    AssistantRuntimeOptions,
    RuntimeCommandSession,
    RuntimeMode,
)
from modules.assistant.workflow import AssistantWorkflow
from modules.voice.command_models import CommandIntent, CommandPath, CommandResult


class CameraStub:
    def __init__(self) -> None:
        self.open_calls = 0
        self.capture_calls = 0
        self.release_calls = 0
        self.source_id = "camera-stub"

    def open(self) -> bool:
        self.open_calls += 1
        return True

    def capture_frame(self):
        self.capture_calls += 1
        return SimpleNamespace(copy=lambda: "frame")

    def release(self) -> None:
        self.release_calls += 1


class ShutdownCommandSession:
    def __init__(self, **kwargs) -> None:
        self._request_shutdown = kwargs["request_shutdown"]
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True
        self._request_shutdown()

    def stop(self) -> None:
        self.stopped = True


class WorkflowStub:
    def __init__(self, result) -> None:
        self.result = result
        self.commands = []
        self.read_calls = []
        self.shutdown_calls = 0
        self.reading_controller = None

    def handle_command(self, command, **kwargs):
        self.commands.append((command, kwargs))
        return self.result

    def run_read_workflow(self, **kwargs):
        self.read_calls.append(kwargs)
        return self.result

    def shutdown(self):
        self.shutdown_calls += 1


def test_runtime_opens_camera_once_and_releases_on_shutdown(capsys):
    camera = CameraStub()
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(startup_checks_enabled=False),
        camera_source=camera,
        workflow=workflow,
        command_session_factory=ShutdownCommandSession,
        startup_check=lambda: 0,
        sleep=lambda _seconds: None,
    )

    assert runtime.run() == 0

    assert camera.open_calls == 1
    assert camera.release_calls == 1
    assert workflow.shutdown_calls == 1
    assert runtime.state == RuntimeMode.SHUTDOWN
    assert "Blind OCR assistant is running" in capsys.readouterr().out


def test_runtime_options_include_configured_camera_source(monkeypatch):
    monkeypatch.setenv("ASSISTANT_CAMERA_SOURCE", "http://192.168.1.4:4747/video")

    options = AssistantRuntimeOptions.from_config(runtime_module.load_config())

    assert options.camera_source == "http://192.168.1.4:4747/video"


def test_runtime_options_include_voice_experience_settings(monkeypatch):
    monkeypatch.setenv("ASSISTANT_VOICE_REPLY_STYLE", "quiet")
    monkeypatch.setenv("ASSISTANT_WELCOME_LANGUAGE", "ar")
    monkeypatch.setenv("ASSISTANT_COMMAND_CONFIRM_EXIT", "false")

    options = AssistantRuntimeOptions.from_config(runtime_module.load_config())

    assert options.voice_reply_style == "quiet"
    assert options.welcome_language == "ar"
    assert options.command_confirm_exit is False


def test_runtime_arabic_welcome_is_spoken_once(capsys):
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(
            startup_checks_enabled=False,
            default_language="ar",
            welcome_language="ar",
        ),
        camera_source=CameraStub(),
        workflow=WorkflowStub(SimpleNamespace(success=True, guidance="ok")),
        startup_check=lambda: 0,
    )

    runtime._announce_welcome()

    assert "المساعد جاهز" in capsys.readouterr().out


def test_runtime_exit_requires_confirmation_by_default():
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(startup_checks_enabled=False),
        camera_source=CameraStub(),
        workflow=WorkflowStub(SimpleNamespace(success=True, guidance="ok")),
        startup_check=lambda: 0,
    )

    first = runtime.dispatch_command("exit")
    assert getattr(first, "success", False) is True
    assert "confirm" in getattr(first, "guidance", "").lower()
    assert runtime._shutdown_requested.is_set() is False

    runtime.dispatch_command("exit")
    assert runtime._shutdown_requested.is_set() is True


def test_runtime_dispatches_read_command_into_searching_mode(capsys):
    result = SimpleNamespace(success=True, guidance="Reading is starting.")
    workflow = WorkflowStub(result)
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(
            startup_checks_enabled=False,
            guided_capture_enabled=False,
        ),
        camera_source=CameraStub(),
        workflow=workflow,
        startup_check=lambda: 0,
    )

    queued = runtime.dispatch_command("read text")

    assert queued.success is True
    assert workflow.read_calls == []
    assert runtime.state == RuntimeMode.SEARCHING_TEXT
    assert "حط النص قدام الكاميرا" in capsys.readouterr().out


def test_translate_before_reading_returns_guidance(capsys):
    workflow = AssistantWorkflow(
        dialogue_manager=DialogueStub(
            CommandResult.recognized(
                intent=CommandIntent.TRANSLATE_TO_ARABIC,
                language="en",
                path=CommandPath.PARSER,
                target_language="ar",
                guidance="Translation command recognized.",
            )
        )
    )
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(startup_checks_enabled=False),
        camera_source=CameraStub(),
        workflow=workflow,
        startup_check=lambda: 0,
    )

    try:
        result = runtime.dispatch_command("translate to arabic")
    finally:
        runtime._job_worker.shutdown()

    assert result.success is True
    assert result.guidance == "Translation job started."
    assert "Translation job started." in capsys.readouterr().out


def test_missing_vosk_model_uses_text_fallback(capsys):
    session = RuntimeCommandSession(
        dispatch_command=lambda _command: None,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model="models/does-not-exist",
        command_timeout_seconds=0.01,
    )

    assert session._can_use_voice() is False
    assert session.mode == "text"
    assert "Text command fallback is active" in capsys.readouterr().out


def test_voice_unknown_command_is_filtered_before_workflow(capsys):
    dispatched = []
    session = RuntimeCommandSession(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model="models/does-not-matter",
        command_timeout_seconds=0.01,
    )

    session._handle_command("random background words", source="voice")
    session._handle_command("random background words", source="voice")

    assert dispatched == []
    assert session.last_status == "Heard unclear audio; waiting for a supported command."
    assert capsys.readouterr().out.count("Heard audio") == 1


def test_text_unknown_command_still_dispatches_for_manual_guidance():
    dispatched = []
    session = RuntimeCommandSession(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=False,
        voice_model=None,
        command_timeout_seconds=0.01,
    )

    session._handle_command("random manual command", source="text")

    assert dispatched == ["random manual command"]


def test_voice_supported_command_dispatches():
    dispatched = []
    session = RuntimeCommandSession(
        dispatch_command=dispatched.append,
        request_shutdown=lambda: None,
        voice_enabled=True,
        voice_model="models/does-not-matter",
        command_timeout_seconds=0.01,
    )

    session._handle_command("read text", source="voice")

    assert dispatched == ["read text"]


def test_runtime_gui_draws_overlay_and_q_requests_shutdown(monkeypatch):
    calls = []

    fake_cv2 = SimpleNamespace(
        FONT_HERSHEY_SIMPLEX=0,
        rectangle=lambda *args, **kwargs: calls.append(("rectangle", args, kwargs)),
        addWeighted=lambda *_args, **_kwargs: None,
        putText=lambda *args, **kwargs: calls.append(("putText", args, kwargs)),
        getTextSize=lambda text, *_args: ((len(str(text)) * 7, 14), 0),
        imshow=lambda name, _frame: calls.append(("imshow", name, None)),
        waitKey=lambda _delay: ord("q"),
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(startup_checks_enabled=False, show_window=True),
        camera_source=CameraStub(),
        workflow=WorkflowStub(SimpleNamespace(success=True, guidance="ok")),
        startup_check=lambda: 0,
    )

    runtime._render_gui(np.zeros((240, 320, 3), dtype=np.uint8))

    assert any(call[0] == "imshow" for call in calls)
    assert runtime._shutdown_requested.is_set()


def test_runtime_uses_latest_frame_for_capture_override_when_quality_gate_is_uncertain():
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(
            startup_checks_enabled=False,
            allow_uncertain_frame=True,
        ),
        camera_source=CameraStub(),
        workflow=WorkflowStub(SimpleNamespace(success=True, guidance="ok")),
        startup_check=lambda: 0,
    )
    runtime._latest_frame = np.zeros((80, 120, 3), dtype=np.uint8)
    runtime._capture_override_active = True

    result = runtime._latest_frame_capture_boundary()

    assert result.success is True
    assert result.selection_result.success is True
    assert result.selection_result.guidance == "Capture override used the latest live frame."
    assert "score" in runtime._latest_quality_status


def test_runtime_quality_analysis_failure_does_not_crash(monkeypatch):
    runtime = AssistantRuntime(
        options=AssistantRuntimeOptions(startup_checks_enabled=False),
        camera_source=CameraStub(),
        workflow=WorkflowStub(SimpleNamespace(success=True, guidance="ok")),
        startup_check=lambda: 0,
    )
    runtime._latest_frame = np.zeros((80, 120, 3), dtype=np.uint8)

    def fail_quality(*_args, **_kwargs):
        raise RuntimeError("opencv memory pressure")

    monkeypatch.setattr(runtime_module, "assess_image_quality", fail_quality)

    result = runtime._latest_frame_capture_boundary()

    assert result.success is False
    assert result.error.error_code.value == "CAMERA_UNEXPECTED_ERROR"
    assert "quality analysis failed" in runtime._latest_quality_status


def test_attempts_status_includes_safe_error_details():
    attempt = SimpleNamespace(
        engine_name="gemini",
        status=SimpleNamespace(value="failed"),
        error_code=SimpleNamespace(value="OCR_PROVIDER_ERROR"),
        safe_metadata={
            "status_code": 503,
            "model": "gemini-2.5-flash-lite",
            "provider_error_status": "UNAVAILABLE",
        },
    )
    result = SimpleNamespace(attempts=[attempt])

    status = runtime_module._attempts_status(result)

    assert status == "gemini:failed:OCR_PROVIDER_ERROR:http=503:UNAVAILABLE"


def test_cue_aware_reading_controller_marks_tts_busy_during_read_all():
    events = []

    class Reader:
        engine = object()

        def start_reading(self, *_args, **_kwargs):
            events.append("read")
            return SimpleNamespace(success=True)

    controller = runtime_module._CueAwareReadingController(
        Reader(),
        before_speak=lambda: events.append("cue_stop"),
        set_tts_busy=lambda busy: events.append(("busy", busy)),
    )

    result = controller.start_reading("text", language="ar")

    assert result.success is True
    assert events == ["cue_stop", ("busy", True), "read", ("busy", False)]


class DialogueStub:
    def __init__(self, result) -> None:
        self.result = result

    def handle_command(self, *_args, **_kwargs):
        return self.result
