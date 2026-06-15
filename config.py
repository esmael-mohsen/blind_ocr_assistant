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


def _read_optional_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


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
    libretranslate_api_key: str = ""
    gemini_api_key: str = ""
    assistant_gemini_ocr_enabled: bool = True
    assistant_gemini_ocr_model: str = "gemini-2.5-flash-lite"
    assistant_gemini_ocr_timeout_seconds: float = 20.0
    assistant_gemini_ocr_fallback_local: bool = True
    assistant_gemini_translation_enabled: bool = True
    assistant_gemini_translation_model: str = "gemini-2.5-flash-lite"
    assistant_gemini_translation_timeout_seconds: float = 20.0
    assistant_camera_source: str = ""
    assistant_camera_index: int = 0
    assistant_voice_enabled: bool = True
    assistant_microphone_index: int | None = None
    assistant_runtime_mode: str = "laptop"
    assistant_command_timeout_seconds: float = 8.0
    assistant_show_window: bool = True
    assistant_default_language: str = "auto"
    assistant_audio_cues_enabled: bool = True
    assistant_guided_capture_enabled: bool = True
    assistant_guided_capture_timeout_seconds: float = 8.0
    assistant_tts_provider: str = "auto"
    assistant_stt_provider: str = "auto"
    assistant_edge_tts_ar_voice: str = "ar-EG-SalmaNeural"
    assistant_edge_tts_en_voice: str = "en-US-JennyNeural"
    assistant_frame_analysis_interval_seconds: float = 0.35
    assistant_stable_text_frames: int = 3
    assistant_text_confidence_threshold: float = 0.55
    assistant_guidance_cooldown_seconds: float = 3.0
    assistant_capture_override_enabled: bool = True
    assistant_quiet_mode: bool = False
    assistant_voice_reply_style: str = "normal"
    assistant_welcome_language: str = "auto"
    assistant_command_confirm_exit: bool = True
    assistant_terminal_logs_enabled: bool = True
    assistant_voice_transcript_logs_enabled: bool = False

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
    _load_dotenv_if_available()
    frame_count = _read_int("FRAME_CAPTURE_COUNT", DEFAULT_FRAME_CAPTURE_COUNT)
    frame_count = max(
        MIN_FRAME_CAPTURE_COUNT, min(MAX_FRAME_CAPTURE_COUNT, frame_count)
    )
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
        libretranslate_api_key=os.getenv("LIBRETRANSLATE_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        assistant_gemini_ocr_enabled=_read_bool(
            "ASSISTANT_GEMINI_OCR_ENABLED",
            True,
        ),
        assistant_gemini_ocr_model=(
            os.getenv("ASSISTANT_GEMINI_OCR_MODEL", "gemini-2.5-flash-lite").strip()
            or "gemini-2.5-flash-lite"
        ),
        assistant_gemini_ocr_timeout_seconds=_read_float(
            "ASSISTANT_GEMINI_OCR_TIMEOUT_SECONDS",
            20.0,
        ),
        assistant_gemini_ocr_fallback_local=_read_bool(
            "ASSISTANT_GEMINI_OCR_FALLBACK_LOCAL",
            True,
        ),
        assistant_gemini_translation_enabled=_read_bool(
            "ASSISTANT_GEMINI_TRANSLATION_ENABLED",
            True,
        ),
        assistant_gemini_translation_model=(
            os.getenv(
                "ASSISTANT_GEMINI_TRANSLATION_MODEL",
                os.getenv("ASSISTANT_GEMINI_OCR_MODEL", "gemini-2.5-flash-lite"),
            ).strip()
            or "gemini-2.5-flash-lite"
        ),
        assistant_gemini_translation_timeout_seconds=_read_float(
            "ASSISTANT_GEMINI_TRANSLATION_TIMEOUT_SECONDS",
            20.0,
        ),
        assistant_camera_source=os.getenv("ASSISTANT_CAMERA_SOURCE", "").strip(),
        assistant_camera_index=_read_int("ASSISTANT_CAMERA_INDEX", 0),
        assistant_voice_enabled=_read_bool("ASSISTANT_VOICE_ENABLED", True),
        assistant_microphone_index=_read_optional_int("ASSISTANT_MICROPHONE_INDEX"),
        assistant_runtime_mode=(
            os.getenv("ASSISTANT_RUNTIME_MODE", "laptop").strip().lower() or "laptop"
        ),
        assistant_command_timeout_seconds=_read_float(
            "ASSISTANT_COMMAND_TIMEOUT_SECONDS",
            8.0,
        ),
        assistant_show_window=_read_bool("ASSISTANT_SHOW_WINDOW", True),
        assistant_default_language=(
            os.getenv("ASSISTANT_DEFAULT_LANGUAGE", "auto").strip().lower() or "auto"
        ),
        assistant_audio_cues_enabled=_read_bool("ASSISTANT_AUDIO_CUES_ENABLED", True),
        assistant_guided_capture_enabled=_read_bool(
            "ASSISTANT_GUIDED_CAPTURE_ENABLED",
            True,
        ),
        assistant_guided_capture_timeout_seconds=_read_float(
            "ASSISTANT_GUIDED_CAPTURE_TIMEOUT_SECONDS",
            8.0,
        ),
        assistant_tts_provider=(
            os.getenv("ASSISTANT_TTS_PROVIDER", "auto").strip().lower() or "auto"
        ),
        assistant_stt_provider=(
            os.getenv("ASSISTANT_STT_PROVIDER", "auto").strip().lower() or "auto"
        ),
        assistant_edge_tts_ar_voice=os.getenv(
            "ASSISTANT_EDGE_TTS_AR_VOICE",
            "ar-EG-SalmaNeural",
        ).strip()
        or "ar-EG-SalmaNeural",
        assistant_edge_tts_en_voice=os.getenv(
            "ASSISTANT_EDGE_TTS_EN_VOICE",
            "en-US-JennyNeural",
        ).strip()
        or "en-US-JennyNeural",
        assistant_frame_analysis_interval_seconds=_read_float(
            "ASSISTANT_FRAME_ANALYSIS_INTERVAL_SECONDS",
            0.35,
        ),
        assistant_stable_text_frames=max(
            1,
            _read_int("ASSISTANT_STABLE_TEXT_FRAMES", 3),
        ),
        assistant_text_confidence_threshold=max(
            0.0,
            min(
                1.0,
                _read_float("ASSISTANT_TEXT_CONFIDENCE_THRESHOLD", 0.55),
            ),
        ),
        assistant_guidance_cooldown_seconds=max(
            0.0,
            _read_float("ASSISTANT_GUIDANCE_COOLDOWN_SECONDS", 3.0),
        ),
        assistant_capture_override_enabled=_read_bool(
            "ASSISTANT_CAPTURE_OVERRIDE_ENABLED",
            True,
        ),
        assistant_quiet_mode=_read_bool("ASSISTANT_QUIET_MODE", False),
        assistant_voice_reply_style=_read_choice(
            "ASSISTANT_VOICE_REPLY_STYLE",
            "normal",
            {"quiet", "normal", "verbose"},
        ),
        assistant_welcome_language=_read_choice(
            "ASSISTANT_WELCOME_LANGUAGE",
            "auto",
            {"auto", "ar", "en"},
        ),
        assistant_command_confirm_exit=_read_bool(
            "ASSISTANT_COMMAND_CONFIRM_EXIT",
            True,
        ),
        assistant_terminal_logs_enabled=_read_bool(
            "ASSISTANT_TERMINAL_LOGS_ENABLED",
            True,
        ),
        assistant_voice_transcript_logs_enabled=_read_bool(
            "ASSISTANT_VOICE_TRANSCRIPT_LOGS_ENABLED",
            False,
        ),
    )


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(PROJECT_ROOT / ".env", override=False)


def _read_choice(name: str, default: str, allowed: set[str]) -> str:
    value = os.getenv(name, default).strip().lower()
    return value if value in allowed else default
