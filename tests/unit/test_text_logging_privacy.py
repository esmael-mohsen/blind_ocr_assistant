"""Phase 5 text logging privacy tests."""

from __future__ import annotations

from modules.text import (
    CleanupWarning,
    DetectedLanguage,
    TextCleanupResult,
    TextCleanupStatus,
    TextDirection,
    sanitize_text_metadata,
    should_include_text_in_logs,
    text_log_metadata,
)


def _result() -> TextCleanupResult:
    return TextCleanupResult(
        success=True,
        raw_text="Sensitive raw OCR text",
        clean_text="Sensitive clean text",
        status=TextCleanupStatus.CLEAN,
        language=DetectedLanguage.ENGLISH,
        direction=TextDirection.LTR,
        warnings=(CleanupWarning.PUNCTUATION_NORMALIZED,),
        guidance="Text is ready for reading.",
        source_engine="paddleocr",
    )


def test_safe_metadata_excludes_text_snippets_secrets_and_debug_paths() -> None:
    metadata = sanitize_text_metadata(
        {
            "raw_text": "private",
            "clean_text": "private",
            "snippet": "private",
            "secret": "private",
            "token": "private",
            "debug_path": "C:/private/text.txt",
            "status": TextCleanupStatus.CLEAN,
            "clean_length": 12,
        }
    )

    assert metadata == {"status": "clean", "clean_length": 12}


def test_default_text_log_metadata_excludes_raw_and_clean_text() -> None:
    metadata = text_log_metadata(_result())

    assert "raw_text" not in metadata
    assert "clean_text" not in metadata
    assert "Sensitive" not in str(metadata)
    assert metadata["status"] == "clean"
    assert metadata["language"] == "english"


def test_text_logs_require_debug_mode_and_sensitive_text_logging() -> None:
    result = _result()

    assert not should_include_text_in_logs(
        debug_mode=False,
        sensitive_text_logging=True,
    )
    assert not should_include_text_in_logs(
        debug_mode=True,
        sensitive_text_logging=False,
    )
    assert should_include_text_in_logs(
        debug_mode=True,
        sensitive_text_logging=True,
    )
    assert "raw_text" not in text_log_metadata(
        result,
        debug_mode=True,
        sensitive_text_logging=False,
    )
    sensitive = text_log_metadata(
        result,
        debug_mode=True,
        sensitive_text_logging=True,
    )
    assert sensitive["raw_text"] == "Sensitive raw OCR text"
    assert sensitive["clean_text"] == "Sensitive clean text"
