"""Tests for Phase 9 assistant state models."""

from __future__ import annotations

import pytest

from modules.assistant.state import (
    AssistantSession,
    AssistantState,
    ReadWorkflowResult,
    SpokenStatus,
    TranslationWorkflowResult,
    WorkflowErrorCode,
    WorkflowFailure,
    WorkflowMode,
    WorkflowRequest,
    WorkflowStatus,
    sanitize_workflow_metadata,
)


def test_assistant_state_tracks_latest_success_and_shutdown_clear():
    state = AssistantState()

    updated = state.with_successful_read(
        raw_text="raw secret text",
        clean_text="clean secret text",
        language="en",
        selected_ocr_engine="ocr_space",
        fallback_used=True,
        guidance="Reading is starting.",
    ).with_successful_translation(
        translated_text="translated secret text",
        guidance="Translation is ready.",
    )

    assert updated.last_raw_text == "raw secret text"
    assert updated.last_clean_text == "clean secret text"
    assert updated.last_translated_text == "translated secret text"
    assert updated.last_language == "en"
    assert updated.last_ocr_engine == "ocr_space"
    assert updated.fallback_used is True
    assert updated.current_mode == WorkflowMode.TRANSLATING
    assert updated.last_guidance == "Translation is ready."

    cleared = updated.clear_for_shutdown()
    assert cleared.current_mode == WorkflowMode.SHUTTING_DOWN
    assert cleared.last_raw_text == ""
    assert cleared.last_clean_text == ""
    assert cleared.last_translated_text == ""
    assert cleared.last_guidance == "Assistant stopped."


def test_workflow_request_and_spoken_status_validate_guidance():
    request = WorkflowRequest(intent="read", language_hint="AR", allow_online=False)
    assert request.language_hint == "ar"
    assert request.allow_online is False
    assert request.request_id.startswith("workflow:")

    status = SpokenStatus(
        category="progress",
        message="Capturing image.",
        workflow_status=WorkflowMode.CAPTURING,
    )
    assert status.requires_speech is True
    assert status.safe_metadata["category"] == "progress"
    assert "message" not in status.safe_metadata

    with pytest.raises(ValueError):
        SpokenStatus(category="progress", message="", workflow_status=WorkflowMode.IDLE)


def test_workflow_failure_requires_guidance_and_safe_metadata():
    failure = WorkflowFailure(
        code=WorkflowErrorCode.CAMERA_UNAVAILABLE,
        message="Camera failed",
        guidance="Camera is unavailable. Try again.",
        source="camera",
    )

    assert failure.recoverable is True
    assert failure.safe_metadata == {
        "error_code": "CAMERA_UNAVAILABLE",
        "recoverable": True,
        "source": "camera",
    }

    with pytest.raises(ValueError):
        WorkflowFailure(
            code=WorkflowErrorCode.OCR_FAILED,
            message="OCR failed",
            guidance="",
        )


def test_read_and_translation_results_require_guidance_and_errors_on_failure():
    read = ReadWorkflowResult.ok(
        selected_ocr_engine="ocr_space",
        language="en",
        fallback_used=False,
        guidance="Reading is starting.",
        raw_text="raw secret",
        clean_text="clean secret",
    )
    assert read.success is True
    assert read.status == WorkflowStatus.SUCCESS
    assert read.reading_started is True
    assert read.safe_metadata["selected_ocr_engine"] == "ocr_space"

    failure = WorkflowFailure(
        WorkflowErrorCode.NO_ACCEPTABLE_FRAME,
        "No frame",
        "Recapture the image.",
    )
    failed_read = ReadWorkflowResult.failure(error=failure)
    assert failed_read.success is False
    assert failed_read.error is failure
    assert failed_read.guidance == "Recapture the image."

    translation = TranslationWorkflowResult.ok(
        target_language="ar",
        source_language="en",
        translated_text="translated secret",
        guidance="The translated text is being read.",
        reading_handoff_attempted=True,
        reading_handoff_success=True,
    )
    assert translation.success is True
    assert translation.translated_text_available is True
    assert translation.safe_metadata["target_language"] == "ar"


def test_safe_metadata_excludes_sensitive_payloads():
    metadata = sanitize_workflow_metadata(
        {
            "image": b"image",
            "depth_map": object(),
            "raw_text": "raw secret",
            "clean_text": "clean secret",
            "translated_text": "translated secret",
            "command_transcript": "read text",
            "speech_input": "audio",
            "snippet": "secret",
            "token": "secret",
            "debug_path": "debug.png",
            "selected_ocr_engine": "ocr_space",
            "fallback_used": True,
            "status": WorkflowStatus.SUCCESS,
        }
    )

    assert metadata == {
        "selected_ocr_engine": "ocr_space",
        "fallback_used": True,
        "status": "success",
    }


def test_assistant_session_blocks_workflows_after_shutdown():
    session = AssistantSession()
    assert session.workflow_active is False
    running = session.with_updates(workflow_active=True)
    assert running.workflow_active is True

    stopped = running.request_shutdown()
    assert stopped.shutdown_requested is True
    assert stopped.workflow_active is False
    assert stopped.state.current_mode == WorkflowMode.SHUTTING_DOWN
