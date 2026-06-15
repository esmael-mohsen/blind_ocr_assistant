"""Privacy-preserving local logging setup."""

from __future__ import annotations

import logging as std_logging
from pathlib import Path
import sys
from typing import Any


LOGGER_NAME = "blind_ocr_assistant"
SENSITIVE_LOG_KEYS = {
    "audio",
    "clean_text",
    "command",
    "image",
    "ocr_text",
    "phrase",
    "raw_text",
    "recognized_phrase",
    "secret",
    "spoken_text",
    "text",
    "token",
    "translated_text",
    "voice_recording",
}


def setup_logging(
    logs_dir: Path,
    level: str = "INFO",
    *,
    console: bool = False,
) -> std_logging.Logger:
    """Configure local operational logging without sensitive content."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = std_logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(std_logging, level.upper(), std_logging.INFO))
    logger.propagate = False

    log_file = logs_dir / "assistant.log"
    formatter = std_logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    existing = [
        handler
        for handler in logger.handlers
        if isinstance(handler, std_logging.FileHandler)
        and Path(handler.baseFilename) == log_file
    ]
    if not existing:
        handler = std_logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if console and not any(getattr(handler, "_assistant_console", False) for handler in logger.handlers):
        console_handler = std_logging.StreamHandler(sys.stdout)
        console_handler._assistant_console = True  # type: ignore[attr-defined]
        console_handler.setFormatter(
            std_logging.Formatter(
                "%(asctime)s | %(levelname)-5s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    return logger


def log_event(
    logger: std_logging.Logger,
    event: str,
    message: str,
    *,
    level: str = "INFO",
) -> None:
    """Write an operational event with non-sensitive context only."""
    numeric_level = getattr(std_logging, level.upper(), std_logging.INFO)
    logger.log(numeric_level, "%s %s", event, message)


def log_kv_event(
    logger: std_logging.Logger,
    event: str,
    /,
    *,
    level: str = "INFO",
    **fields: Any,
) -> None:
    """Log one safe structured event as stable key=value pairs."""
    message = " ".join(
        f"{key}={_safe_value(key, value)}"
        for key, value in fields.items()
        if value is not None
    )
    log_event(logger, event, message, level=level)


def _safe_value(key: str, value: Any) -> str:
    if key.lower() in SENSITIVE_LOG_KEYS:
        text = "" if value is None else str(value)
        return f"<redacted:length={len(text)}>"
    raw = getattr(value, "value", value)
    if isinstance(raw, float):
        return f"{raw:.3f}"
    text = str(raw).replace("\n", "\\n").replace("\r", "\\r")
    if not text:
        return "empty"
    if " " in text:
        text = repr(text)
    return text[:180]
