"""Phase 0 configuration defaults for Blind OCR Assistant."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

LOGS_DIR = PROJECT_ROOT / "logs"
DEBUG_CAPTURES_DIR = PROJECT_ROOT / "debug_captures"
BENCHMARK_RESULTS_DIR = PROJECT_ROOT / "benchmark_results"
CONFIG_DIR = PROJECT_ROOT / "config"

SUPPORTED_LANGUAGES = ("ar", "en")
DEFAULT_FRAME_CAPTURE_COUNT = 15
MIN_FRAME_CAPTURE_COUNT = 1
MAX_FRAME_CAPTURE_COUNT = 20


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    """Central Phase 0 configuration with privacy-preserving defaults."""

    languages: tuple[str, ...] = SUPPORTED_LANGUAGES
    online_first: bool = True
    offline_fallback: bool = True
    debug_save_images: bool = False
    sensitive_text_logging: bool = False
    log_level: str = "INFO"
    frame_capture_count: int = DEFAULT_FRAME_CAPTURE_COUNT
    logs_dir: Path = LOGS_DIR
    debug_captures_dir: Path = DEBUG_CAPTURES_DIR
    benchmark_results_dir: Path = BENCHMARK_RESULTS_DIR
    config_dir: Path = CONFIG_DIR
    ocr_space_api_key: str = ""
    libretranslate_url: str = ""

    @property
    def runtime_dirs(self) -> tuple[Path, ...]:
        return (
            self.logs_dir,
            self.debug_captures_dir,
            self.benchmark_results_dir,
            self.config_dir,
        )


def load_config() -> AppConfig:
    """Load Phase 0 config from environment without requiring any secrets."""
    frame_count = _read_int("FRAME_CAPTURE_COUNT", DEFAULT_FRAME_CAPTURE_COUNT)
    frame_count = max(MIN_FRAME_CAPTURE_COUNT, min(MAX_FRAME_CAPTURE_COUNT, frame_count))
    return AppConfig(
        debug_save_images=_read_bool("DEBUG_SAVE_IMAGES", False),
        sensitive_text_logging=_read_bool("SENSITIVE_TEXT_LOGGING", False),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        frame_capture_count=frame_count,
        ocr_space_api_key=os.getenv("OCR_SPACE_API_KEY", ""),
        libretranslate_url=os.getenv("LIBRETRANSLATE_URL", ""),
    )

