"""Tests for runtime event-driven controller."""

from __future__ import annotations

from types import SimpleNamespace

from modules.assistant.job_worker import JobWorker
from modules.assistant.runtime_controller import RuntimeController, RuntimeControllerMode
from modules.assistant.runtime_state import FrameReadiness


class WorkflowStub:
    def __init__(self, result):
        self.result = result
        self.read_calls = []
        self.command_calls = []
        self.reading_controller = SimpleNamespace(stop=lambda: SimpleNamespace(success=True, guidance="stopped"))

    def run_read_workflow(self, **kwargs):
        self.read_calls.append(kwargs)
        return self.result

    def handle_command(self, command, **kwargs):
        self.command_calls.append((command, kwargs))
        return self.result

    def get_state(self):
        return SimpleNamespace(last_language="en", last_clean_text="text")


class ImmediateJobWorker(JobWorker):
    def __init__(self) -> None:
        self.submitted = []
        self._active_job = None

    @property
    def active_job(self):
        return self._active_job

    def submit(self, job_type, func, *, progress_label, on_complete=None):
        self.submitted.append((job_type, progress_label))
        result = func()
        job = SimpleNamespace(job_type=job_type, status=SimpleNamespace(value="succeeded"), finished_at=1.0)
        if on_complete:
            on_complete(job, result)
        return job

    def cancel_active(self):
        return False

    def shutdown(self):
        return None


def _controller(workflow, *, worker=None):
    modes = []
    cues = []
    spoken = []
    controller = RuntimeController(
        workflow=workflow,
        capture_preview=lambda: SimpleNamespace(selection_result=None, candidates=[]),
        speak=lambda text, language: spoken.append((text, language)),
        set_mode=modes.append,
        start_cue=cues.append,
        stop_cue=lambda: cues.append("stop"),
        job_worker=worker or ImmediateJobWorker(),
        guidance_cooldown_seconds=0.0,
    )
    return controller, modes, cues, spoken


def test_read_text_enters_searching_without_running_ocr():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="Reading is starting."))
    controller, modes, _cues, spoken = _controller(workflow)

    result = controller.handle_command("read text", high_accuracy=True)

    assert result.success is True
    assert workflow.read_calls == []
    assert controller.waiting_for_text is True
    assert RuntimeControllerMode.SEARCHING_TEXT in modes
    assert spoken


def test_not_ready_frame_does_not_submit_ocr_job():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    worker = ImmediateJobWorker()
    controller, _modes, _cues, _spoken = _controller(workflow, worker=worker)

    controller.handle_command("read text")
    controller.on_frame_readiness(
        FrameReadiness(has_text=False, ready_to_capture=False, guidance_code="no_text")
    )

    assert workflow.read_calls == []
    assert worker.submitted == []


def test_no_text_guidance_does_not_repeat_immediately():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    controller, _modes, _cues, spoken = _controller(workflow)

    controller.handle_command("read text")
    controller.on_frame_readiness(
        FrameReadiness(has_text=False, ready_to_capture=False, guidance_code="no_text")
    )

    assert len(spoken) == 1


def test_ready_frame_submits_ocr_job_and_stops_cue():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    worker = ImmediateJobWorker()
    controller, modes, cues, _spoken = _controller(workflow, worker=worker)

    controller.handle_command("read text", high_accuracy=True)
    controller.on_frame_readiness(
        FrameReadiness(
            has_text=True,
            ready_to_capture=True,
            stable_frames=3,
            guidance_code="ready",
        )
    )

    assert workflow.read_calls == [{"high_accuracy": True}]
    assert worker.submitted
    assert "ocr" in cues
    assert "stop" in cues
    assert modes[-1] == RuntimeControllerMode.LISTENING


def test_low_quality_ready_frame_uses_capture_override():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    override_values = []
    controller, _modes, _cues, _spoken = _controller(workflow)
    controller.set_capture_override = override_values.append

    controller.handle_command("read text")
    controller.on_frame_readiness(
        FrameReadiness(
            has_text=True,
            ready_to_capture=True,
            stable_frames=3,
            guidance_code="ready_low_quality",
        )
    )

    assert workflow.read_calls == [{"high_accuracy": False}]
    assert override_values == [True, False]


def test_search_timeout_captures_visible_stable_text_without_waiting_forever():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    override_values = []
    controller, _modes, _cues, _spoken = _controller(workflow)
    controller.guided_capture_timeout_seconds = 0.01
    controller.set_capture_override = override_values.append

    controller.handle_command("read text")
    controller._search_started_at -= 1.0
    controller.on_frame_readiness(
        FrameReadiness(
            has_text=True,
            ready_to_capture=False,
            stable_frames=2,
            guidance_code="blurry",
            guidance="Hold steady.",
        )
    )

    assert workflow.read_calls == [{"high_accuracy": False}]
    assert override_values == [True, False]


def test_capture_now_overrides_readiness_gate():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    override_values = []
    controller, _modes, _cues, _spoken = _controller(workflow)
    controller.set_capture_override = override_values.append

    result = controller.handle_command("capture now", high_accuracy=False)

    assert result.success is True
    assert workflow.read_calls == [{"high_accuracy": False}]
    assert override_values == [True, False]


def test_translate_command_runs_as_background_job():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="translated"))
    worker = ImmediateJobWorker()
    controller, _modes, cues, _spoken = _controller(workflow, worker=worker)

    result = controller.handle_command("translate to arabic")

    assert result.success is True
    assert workflow.command_calls[0][0] == "translate to arabic"
    assert cues == ["translation", "stop"]


def test_translate_guidance_uses_command_language_not_current_language():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="translated"))
    worker = ImmediateJobWorker()
    controller, _modes, _cues, spoken = _controller(workflow, worker=worker)
    controller.language = "ar"

    result = controller.handle_command("translate to english")

    assert result.success is True
    assert ("Translating now.", "en") in spoken


def test_successful_translation_completion_is_announced_when_not_read_aloud():
    workflow = WorkflowStub(
        SimpleNamespace(
            success=True,
            guidance="Translation is ready.",
            reading_handoff_success=False,
        )
    )
    controller, _modes, _cues, spoken = _controller(workflow, worker=ImmediateJobWorker())

    result = controller.handle_command("translate to arabic")

    assert result.success is True
    assert ("Translation is ready.", "en") in spoken


def test_switch_arabic_updates_runtime_language_callback():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    controller, _modes, _cues, spoken = _controller(workflow)
    changed = []
    controller.on_language_change = changed.append

    result = controller.handle_command("switch arabic")

    assert result.success is True
    assert changed == ["ar"]
    assert spoken[-1][1] == "ar"


def test_voice_test_speaks_english_and_arabic_samples():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    controller, _modes, _cues, spoken = _controller(workflow)

    result = controller.handle_command("voice test")

    assert result.success is True
    assert spoken[-2][1] == "en"
    assert spoken[-1][1] == "ar"


def test_status_and_what_do_you_see_use_latest_state():
    workflow = WorkflowStub(SimpleNamespace(success=True, guidance="ok"))
    controller, _modes, _cues, spoken = _controller(workflow)
    controller.on_frame_readiness(FrameReadiness(has_text=False, guidance="No text yet."))

    status = controller.handle_command("status")
    frame = controller.handle_command("what do you see")

    assert status.success is True
    assert "Text ready: True" in status.guidance
    assert "No text yet" in frame.guidance
    assert spoken
