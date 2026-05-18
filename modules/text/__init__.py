"""Text processing package."""

from modules.text.cleanup import (
    CleanupWarning,
    DetectedLanguage,
    TextCleanupRequest,
    TextCleanupResult,
    TextCleanupStatus,
    TextDirection,
    clean_ocr_text,
    sanitize_text_metadata,
    should_include_text_in_logs,
    text_log_metadata,
)
from modules.text.language_detector import (
    DirectionInfo,
    LanguageDetectionResult,
    detect_language,
)
from modules.text.rtl_fixer import detect_text_direction, preserve_logical_order
from modules.text.rtl_fixer import __all__ as _rtl_exports
from modules.text.segmentation import split_paragraphs, split_sentences
from modules.text.segmentation import __all__ as _segmentation_exports

__all__ = [
    "CleanupWarning",
    "DetectedLanguage",
    "DirectionInfo",
    "LanguageDetectionResult",
    "TextCleanupRequest",
    "TextCleanupResult",
    "TextCleanupStatus",
    "TextDirection",
    "clean_ocr_text",
    "detect_text_direction",
    "detect_language",
    "preserve_logical_order",
    "sanitize_text_metadata",
    "should_include_text_in_logs",
    "split_paragraphs",
    "split_sentences",
    "text_log_metadata",
    *_rtl_exports,
    *_segmentation_exports,
]
