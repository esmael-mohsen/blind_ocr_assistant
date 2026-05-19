"""Manual eSpeak NG smoke-test entrypoint for Phase 6."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.voice.tts_engine import EspeakNGEngine, TTSEngine  # noqa: E402
from modules.voice.voice_models import (  # noqa: E402
    SpeechOperation,
    SpeechRequest,
    SpeechResult,
    TTSError,
    TTSErrorCode,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the TTS smoke-test argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a local eSpeak NG smoke test without printing text content. "
            "For Phase 11 speaker diagnostics, also run "
            "scripts/pi_deployment_check.py --full."
        )
    )
    parser.add_argument("--text", required=True, help="Clean text to speak")
    parser.add_argument(
        "--language",
        default="mixed",
        choices=("ar", "en", "mixed"),
        help="Language metadata for the speech engine",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=None,
        help="Optional speech rate in words per minute",
    )
    return parser


def run_smoke_test(
    argv: Sequence[str] | None = None,
    *,
    engine_factory: Callable[[], TTSEngine] = EspeakNGEngine,
) -> int:
    """Run the smoke test and print safe structured output."""
    args = build_parser().parse_args(argv)
    try:
        request = SpeechRequest(
            text=args.text,
            language=args.language,
            rate_wpm=args.rate,
            operation=SpeechOperation.READ_ALL,
        )
    except ValueError:
        result = SpeechResult.failure(
            operation=SpeechOperation.READ_ALL,
            engine_name=None,
            error=TTSError(
                code=TTSErrorCode.NO_READABLE_TEXT,
                message="No readable text was provided",
            ),
            guidance="No readable text is available.",
        )
        _print_result(result)
        return 1

    result = engine_factory().speak(request)
    _print_result(result)
    return 0 if result.success else 1


def _print_result(result: SpeechResult) -> None:
    payload = {
        "success": result.success,
        "operation": result.operation.value,
        "engine_name": result.engine_name,
        "duration_ms": result.duration_ms,
        "fallback_used": result.fallback_used,
        "error_code": result.error.code.value if result.error else None,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    return run_smoke_test(argv)


if __name__ == "__main__":
    raise SystemExit(main())
