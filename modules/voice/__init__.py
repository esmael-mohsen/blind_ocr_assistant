"""Voice package exports."""

from modules.voice.tts_engine import EspeakNGEngine, MockTTSEngine, TTSEngine
from modules.voice.voice_models import (
    DEFAULT_SPEECH_RATE_WPM,
    MAX_SPEECH_RATE_WPM,
    MIN_SPEECH_RATE_WPM,
    ReadingControlCommand,
    ReadingControlType,
    ReadingState,
    SegmentType,
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
    TextSegment,
    clamp_speech_rate,
    sanitize_speech_metadata,
)

__all__ = [
    "DEFAULT_SPEECH_RATE_WPM",
    "EspeakNGEngine",
    "MAX_SPEECH_RATE_WPM",
    "MIN_SPEECH_RATE_WPM",
    "MockTTSEngine",
    "ReadingControlCommand",
    "ReadingControlType",
    "ReadingState",
    "SegmentType",
    "SpeechOperation",
    "SpeechRequest",
    "SpeechResult",
    "TTSError",
    "TTSErrorCode",
    "TTSEngine",
    "TextSegment",
    "clamp_speech_rate",
    "sanitize_speech_metadata",
]
