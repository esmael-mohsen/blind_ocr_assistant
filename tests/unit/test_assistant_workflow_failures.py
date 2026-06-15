"""Failure-path tests for Phase 9 assistant workflow orchestration."""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from modules.assistant.state import WorkflowErrorCode
from modules.assistant.workflow import AssistantWorkflow


def test_boundary_wrapper_converts_timeout_to_workflow_failure():
    workflow = AssistantWorkflow()

    def raises_timeout():
        raise TimeoutError("too slow")

    result = workflow._call_boundary(
        raises_timeout,
        failure_code=WorkflowErrorCode.COMPONENT_TIMEOUT,
        failure_guidance="The operation timed out.",
        failure_message="Timed out",
    )

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.COMPONENT_TIMEOUT
    assert result.guidance == "The operation timed out."


def test_boundary_wrapper_converts_unexpected_exception_to_workflow_failure():
    workflow = AssistantWorkflow()

    def raises_error():
        raise RuntimeError("secret text should not leak")

    result = workflow._call_boundary(
        raises_error,
        failure_code=WorkflowErrorCode.WORKFLOW_UNEXPECTED_ERROR,
        failure_guidance="Workflow failed. Try again.",
        failure_message="Workflow failed",
    )

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.WORKFLOW_UNEXPECTED_ERROR
    assert "secret text" not in result.guidance


def test_boundary_wrapper_reraises_keyboard_interrupt():
    workflow = AssistantWorkflow()

    def raises_interrupt():
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        workflow._call_boundary(
            raises_interrupt,
            failure_code=WorkflowErrorCode.WORKFLOW_UNEXPECTED_ERROR,
            failure_guidance="Workflow failed.",
            failure_message="Workflow failed",
        )


def test_missing_required_boundary_returns_structured_failure():
    workflow = AssistantWorkflow()

    result = workflow._missing_boundary(
        code=WorkflowErrorCode.CAMERA_UNAVAILABLE,
        guidance="Camera is unavailable.",
        source="camera",
    )

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.CAMERA_UNAVAILABLE
    assert result.error.source == "camera"


def test_translation_without_latest_clean_text_returns_guidance():
    translation = object()
    workflow = AssistantWorkflow(translation_controller=translation)

    result = workflow.run_translation_workflow("en")

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.TRANSLATION_UNAVAILABLE
    assert "No readable text" in result.guidance


def test_translation_failure_preserves_previous_state():
    class TranslationStub:
        def translate_latest(self, *args, **kwargs):
            return type(
                "Result",
                (),
                {
                    "success": False,
                    "guidance": "Translation failed.",
                    "fallback_used": True,
                    "duration_ms": 5,
                },
            )()

    workflow = AssistantWorkflow(translation_controller=TranslationStub())
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="raw",
            clean_text="clean",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Read.",
        ).with_successful_translation(
            translated_text="old translation",
            guidance="Old translation.",
        )
    )

    result = workflow.run_translation_workflow("ar")

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.TRANSLATION_FAILED
    assert workflow.get_state().last_clean_text == "clean"
    assert workflow.get_state().last_translated_text == "old translation"


class Boundary:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.result


class ReadingStub:
    def __init__(self, success=True):
        self.success = success

    def start_reading(self, *args, **kwargs):
        return SimpleNamespace(success=self.success, guidance="Reading failed.")


def test_camera_capture_failure_returns_guidance_and_preserves_responsiveness():
    workflow = AssistantWorkflow(
        capture_burst=Boundary(
            SimpleNamespace(
                success=False,
                message="Camera failed.",
                error=SimpleNamespace(guidance="Camera is unavailable. Try again."),
            )
        ),
        run_ocr_cascade=Boundary(),
        clean_ocr_text=Boundary(),
        reading_controller=ReadingStub(),
    )

    result = workflow.run_read_workflow()

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.CAMERA_UNAVAILABLE
    assert "Camera" in result.guidance
    assert workflow.session.workflow_active is False


def test_camera_capture_timeout_result_maps_to_capture_timeout():
    workflow = AssistantWorkflow(
        capture_burst=Boundary(
            SimpleNamespace(
                success=False,
                message="Camera timed out.",
                error=SimpleNamespace(
                    error_code="CAMERA_CAPTURE_TIMEOUT",
                    guidance="Camera timed out. Try again.",
                ),
            )
        ),
        run_ocr_cascade=Boundary(),
        clean_ocr_text=Boundary(),
        reading_controller=ReadingStub(),
    )

    result = workflow.run_read_workflow()

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.CAPTURE_TIMEOUT
    assert "timed out" in result.guidance


def test_all_frames_rejected_returns_recapture_guidance_and_no_auto_loop():
    frame = SimpleNamespace(rgb_image=b"bad image")
    capture = Boundary(
        SimpleNamespace(
            success=True,
            candidates=[frame],
            selection_result=SimpleNamespace(
                success=False,
                guidance="Recapture the image more clearly.",
            ),
        )
    )
    ocr = Boundary()
    workflow = AssistantWorkflow(
        capture_burst=capture,
        run_ocr_cascade=ocr,
        clean_ocr_text=Boundary(),
        reading_controller=ReadingStub(),
    )

    result = workflow.run_read_workflow()

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.NO_ACCEPTABLE_FRAME
    assert "Recapture" in result.guidance
    assert len(capture.calls) == 1
    assert ocr.calls == []


def test_ocr_failure_and_no_text_return_readable_guidance():
    frame = SimpleNamespace(rgb_image=b"image")
    workflow = AssistantWorkflow(
        capture_burst=Boundary(
            SimpleNamespace(
                success=True,
                candidates=[frame],
                selection_result=SimpleNamespace(success=True, selected_frame=frame),
            )
        ),
        run_ocr_cascade=Boundary(
            SimpleNamespace(
                success=False,
                guidance="I could not read the text clearly. Please try again.",
            )
        ),
        clean_ocr_text=Boundary(),
        reading_controller=ReadingStub(),
    )

    result = workflow.run_read_workflow()

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.OCR_FAILED
    assert "read the text" in result.guidance


def test_cleanup_empty_text_and_tts_failure_return_structured_guidance():
    frame = SimpleNamespace(rgb_image=b"image")
    workflow = AssistantWorkflow(
        capture_burst=Boundary(
            SimpleNamespace(
                success=True,
                candidates=[frame],
                selection_result=SimpleNamespace(success=True, selected_frame=frame),
            )
        ),
        run_ocr_cascade=Boundary(
            SimpleNamespace(
                success=True,
                selected_engine="ocr_space",
                selected_result=SimpleNamespace(raw_text="###"),
                fallback_used=False,
                offline_route_used=False,
                high_accuracy_used=False,
            )
        ),
        clean_ocr_text=Boundary(
            SimpleNamespace(success=True, clean_text="", guidance="No readable text was available.")
        ),
        reading_controller=ReadingStub(),
    )

    cleanup_result = workflow.run_read_workflow()
    assert cleanup_result.error.code == WorkflowErrorCode.CLEANUP_EMPTY_TEXT

    workflow.clean_ocr_text = Boundary(
        SimpleNamespace(
            success=True,
            raw_text="raw",
            clean_text="clean",
            language="english",
            guidance="Text ready.",
        )
    )
    workflow.reading_controller = ReadingStub(success=False)

    tts_result = workflow.run_read_workflow()
    assert tts_result.success is True
    assert tts_result.ocr_success is True
    assert tts_result.reading_started is False
    assert tts_result.selected_ocr_engine == "ocr_space"
    assert workflow.get_state().last_clean_text == "clean"
    assert "speech" in tts_result.guidance.lower()


def test_component_timeout_and_unexpected_exception_keep_previous_state():
    workflow = AssistantWorkflow()
    workflow.session = workflow.session.with_updates(
        state=workflow.session.state.with_successful_read(
            raw_text="previous raw",
            clean_text="previous clean",
            language="en",
            selected_ocr_engine="ocr_space",
            fallback_used=False,
            guidance="Previous read.",
        ).with_successful_translation(
            translated_text="previous translation",
            guidance="Previous translation.",
        )
    )

    def timeout_capture():
        raise TimeoutError("slow")

    workflow.capture_burst = timeout_capture
    workflow.run_ocr_cascade = Boundary()
    workflow.clean_ocr_text = Boundary()
    workflow.reading_controller = ReadingStub()

    result = workflow.run_read_workflow()

    assert result.error.code == WorkflowErrorCode.COMPONENT_TIMEOUT
    assert workflow.get_state().last_clean_text == "previous clean"
    assert workflow.get_state().last_translated_text == "previous translation"


def test_shutdown_cleanup_hook_failure_returns_resource_release_failure():
    def bad_cleanup():
        raise RuntimeError("cleanup failed")

    workflow = AssistantWorkflow(cleanup_hooks=[bad_cleanup])

    result = workflow.shutdown()

    assert result.success is False
    assert result.error.code == WorkflowErrorCode.RESOURCE_RELEASE_FAILED
    assert workflow.session.shutdown_requested is True
    assert workflow.session.workflow_active is False
