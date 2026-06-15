"""Local operational logging tests."""

from __future__ import annotations

from modules.common.logging import log_event, log_kv_event, setup_logging


def test_setup_logging_writes_local_operational_events(tmp_path) -> None:
    logger = setup_logging(tmp_path, "INFO")

    log_event(logger, "BOOTSTRAP_TEST", "operational event only")

    log_file = tmp_path / "assistant.log"
    content = log_file.read_text(encoding="utf-8")
    assert "BOOTSTRAP_TEST operational event only" in content
    assert "raw_text" not in content
    assert "clean_text" not in content
    assert "voice_recording" not in content


def test_runtime_kv_logging_redacts_sensitive_fields(tmp_path) -> None:
    logger = setup_logging(tmp_path, "INFO")

    log_kv_event(
        logger,
        "RUNTIME_TEST",
        mode="SEARCHING_TEXT",
        clean_text="private text",
        quality_score=0.65,
    )

    content = (tmp_path / "assistant.log").read_text(encoding="utf-8")
    assert "RUNTIME_TEST" in content
    assert "mode=SEARCHING_TEXT" in content
    assert "quality_score=0.650" in content
    assert "private text" not in content
    assert "clean_text=<redacted:length=12>" in content
