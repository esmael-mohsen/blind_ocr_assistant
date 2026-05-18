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
DEFAULT_CAMERA_FRAME_CAPTURE_COUNT = 15
MIN_CAMERA_FRAME_CAPTURE_COUNT = 10
MAX_CAMERA_FRAME_CAPTURE_COUNT = 20
DEFAULT_CAMERA_CAPTURE_TIMEOUT_SECONDS = 3.0
DEFAULT_CAMERA_PREFER_DEPTH = True
DEFAULT_CAMERA_ALLOW_RGB_FALLBACK = True
DEFAULT_CAMERA_DEPTH_TOO_CLOSE_CM = 25.0
DEFAULT_CAMERA_DEPTH_TOO_FAR_CM = 75.0
DEFAULT_OCR_TIMEOUT_SECONDS = 10.0
DEFAULT_OCR_RETRY_COUNT = 1
DEFAULT_OCR_QUALITY_THRESHOLD = 0.70
DEFAULT_OCR_MAX_ATTEMPTS_PER_ENGINE = 1
DEFAULT_OCR_HIGH_ACCURACY_TIE_DELTA = 0.05
DEFAULT_OCR_ONLINE_AVAILABILITY_TIMEOUT_SECONDS = 2.0
DEFAULT_MIN_BRIGHTNESS = 45.0
DEFAULT_MAX_BRIGHTNESS = 235.0
DEFAULT_MIN_SHARPNESS = 60.0
DEFAULT_MIN_CONTRAST = 25.0
DEFAULT_MIN_TEXT_PRESENCE = 0.12
DEFAULT_MIN_IMAGE_QUALITY_SCORE = 0.6


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


def _read_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
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
    camera_frame_capture_count: int = DEFAULT_CAMERA_FRAME_CAPTURE_COUNT
    camera_capture_timeout_seconds: float = DEFAULT_CAMERA_CAPTURE_TIMEOUT_SECONDS
    camera_prefer_depth: bool = DEFAULT_CAMERA_PREFER_DEPTH
    camera_allow_rgb_fallback: bool = DEFAULT_CAMERA_ALLOW_RGB_FALLBACK
    camera_depth_too_close_cm: float = DEFAULT_CAMERA_DEPTH_TOO_CLOSE_CM
    camera_depth_too_far_cm: float = DEFAULT_CAMERA_DEPTH_TOO_FAR_CM
    ocr_timeout_seconds: float = DEFAULT_OCR_TIMEOUT_SECONDS
    ocr_retry_count: int = DEFAULT_OCR_RETRY_COUNT
    ocr_quality_threshold: float = DEFAULT_OCR_QUALITY_THRESHOLD
    ocr_max_attempts_per_engine: int = DEFAULT_OCR_MAX_ATTEMPTS_PER_ENGINE
    ocr_high_accuracy_tie_delta: float = DEFAULT_OCR_HIGH_ACCURACY_TIE_DELTA
    ocr_online_availability_timeout_seconds: float = (
        DEFAULT_OCR_ONLINE_AVAILABILITY_TIMEOUT_SECONDS
    )
    min_brightness: float = DEFAULT_MIN_BRIGHTNESS
    max_brightness: float = DEFAULT_MAX_BRIGHTNESS
    min_sharpness: float = DEFAULT_MIN_SHARPNESS
    min_contrast: float = DEFAULT_MIN_CONTRAST
    min_text_presence: float = DEFAULT_MIN_TEXT_PRESENCE
    min_image_quality_score: float = DEFAULT_MIN_IMAGE_QUALITY_SCORE
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
    camera_frame_count = _read_int(
        "CAMERA_FRAME_CAPTURE_COUNT",
        DEFAULT_CAMERA_FRAME_CAPTURE_COUNT,
    )
    camera_frame_count = max(
        MIN_CAMERA_FRAME_CAPTURE_COUNT,
        min(MAX_CAMERA_FRAME_CAPTURE_COUNT, camera_frame_count),
    )
    return AppConfig(
        debug_save_images=_read_bool("DEBUG_SAVE_IMAGES", False),
        sensitive_text_logging=_read_bool("SENSITIVE_TEXT_LOGGING", False),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        frame_capture_count=frame_count,
        camera_frame_capture_count=camera_frame_count,
        camera_capture_timeout_seconds=_read_float(
            "CAMERA_CAPTURE_TIMEOUT_SECONDS",
            DEFAULT_CAMERA_CAPTURE_TIMEOUT_SECONDS,
        ),
        camera_prefer_depth=_read_bool(
            "CAMERA_PREFER_DEPTH",
            DEFAULT_CAMERA_PREFER_DEPTH,
        ),
        camera_allow_rgb_fallback=_read_bool(
            "CAMERA_ALLOW_RGB_FALLBACK",
            DEFAULT_CAMERA_ALLOW_RGB_FALLBACK,
        ),
        camera_depth_too_close_cm=_read_float(
            "CAMERA_DEPTH_TOO_CLOSE_CM",
            DEFAULT_CAMERA_DEPTH_TOO_CLOSE_CM,
        ),
        camera_depth_too_far_cm=_read_float(
            "CAMERA_DEPTH_TOO_FAR_CM",
            DEFAULT_CAMERA_DEPTH_TOO_FAR_CM,
        ),
        ocr_timeout_seconds=float(
            os.getenv("OCR_TIMEOUT_SECONDS", DEFAULT_OCR_TIMEOUT_SECONDS)
        ),
        ocr_retry_count=max(0, _read_int("OCR_RETRY_COUNT", DEFAULT_OCR_RETRY_COUNT)),
        ocr_quality_threshold=_read_float(
            "OCR_QUALITY_THRESHOLD",
            DEFAULT_OCR_QUALITY_THRESHOLD,
        ),
        ocr_max_attempts_per_engine=max(
            1,
            _read_int(
                "OCR_MAX_ATTEMPTS_PER_ENGINE",
                DEFAULT_OCR_MAX_ATTEMPTS_PER_ENGINE,
            ),
        ),
        ocr_high_accuracy_tie_delta=_read_float(
            "OCR_HIGH_ACCURACY_TIE_DELTA",
            DEFAULT_OCR_HIGH_ACCURACY_TIE_DELTA,
        ),
        ocr_online_availability_timeout_seconds=_read_float(
            "OCR_ONLINE_AVAILABILITY_TIMEOUT_SECONDS",
            DEFAULT_OCR_ONLINE_AVAILABILITY_TIMEOUT_SECONDS,
        ),
        min_brightness=_read_float("IMAGE_MIN_BRIGHTNESS", DEFAULT_MIN_BRIGHTNESS),
        max_brightness=_read_float("IMAGE_MAX_BRIGHTNESS", DEFAULT_MAX_BRIGHTNESS),
        min_sharpness=_read_float("IMAGE_MIN_SHARPNESS", DEFAULT_MIN_SHARPNESS),
        min_contrast=_read_float("IMAGE_MIN_CONTRAST", DEFAULT_MIN_CONTRAST),
        min_text_presence=_read_float(
            "IMAGE_MIN_TEXT_PRESENCE",
            DEFAULT_MIN_TEXT_PRESENCE,
        ),
        min_image_quality_score=_read_float(
            "IMAGE_MIN_QUALITY_SCORE",
            DEFAULT_MIN_IMAGE_QUALITY_SCORE,
        ),
        ocr_space_api_key=os.getenv("OCR_SPACE_API_KEY", ""),
        libretranslate_url=os.getenv("LIBRETRANSLATE_URL", ""),
    )
