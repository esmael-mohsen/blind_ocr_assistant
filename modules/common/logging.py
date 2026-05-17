"""Privacy-preserving local logging setup."""

from __future__ import annotations

import logging as std_logging
from pathlib import Path


LOGGER_NAME = "blind_ocr_assistant"


def setup_logging(logs_dir: Path, level: str = "INFO") -> std_logging.Logger:
    """Configure local operational logging without sensitive content."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = std_logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(std_logging, level.upper(), std_logging.INFO))
    logger.propagate = False

    log_file = logs_dir / "assistant.log"
    formatter = std_logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

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

